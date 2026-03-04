from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Course, Group, Enrollment
from .forms import CourseForm, GroupForm, EnrollmentForm
from accounts.permissions import admin_required, teacher_required
import openpyxl
from django.http import HttpResponse


# ──────────── COURSES ────────────
@login_required
def course_list(request):
    courses = Course.objects.all()
    return render(request, 'courses/course_list.html', {'courses': courses})

@admin_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f"'{course.name}' kursi qo'shildi!")
            return redirect('courses:course_list')
    else:
        form = CourseForm()
    return render(request, 'courses/course_form.html', {'form': form, 'title': 'Yangi kurs'})


@admin_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Kurs yangilandi!')
            return redirect('courses:course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/course_form.html', {'form': form, 'title': 'Kursni tahrirlash', 'obj': course})


@admin_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Kurs o\'chirildi!')
        return redirect('courses:course_list')
    return render(request, 'courses/confirm_delete.html', {'obj': course, 'title': 'Kursni o\'chirish'})


# ──────────── GROUPS ────────────
@login_required
def group_list(request):
    if request.user.is_admin_role:
        groups = Group.objects.select_related('course', 'teacher').all()
    elif request.user.is_teacher:
        groups = Group.objects.filter(teacher__user=request.user).select_related('course', 'teacher')
    elif request.user.is_student:
        groups = Group.objects.filter(enrollments__student__user=request.user, enrollments__is_active=True).select_related('course', 'teacher')
    else:
        groups = Group.objects.none()
    return render(request, 'courses/group_list.html', {'groups': groups})


@login_required
def group_detail(request, pk):
    group = get_object_or_404(Group.objects.select_related('course', 'teacher'), pk=pk)
    
    # Permission check
    if not request.user.is_admin_role:
        if request.user.is_teacher and group.teacher.user != request.user:
            messages.error(request, "Bu guruhga kirish huquqingiz yo'q!")
            return redirect('courses:group_list')
        if request.user.is_student and not group.enrollments.filter(student__user=request.user, is_active=True).exists():
            messages.error(request, "Siz ushbu guruhga a'zo emassiz!")
            return redirect('courses:group_list')

    enrollments = group.enrollments.filter(is_active=True).select_related('student')
    return render(request, 'courses/group_detail.html', {
        'group': group,
        'enrollments': enrollments,
    })


@admin_required
def group_create(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            messages.success(request, f"'{group.name}' guruhi yaratildi!")
            return redirect('courses:group_list')
    else:
        form = GroupForm()
    return render(request, 'courses/group_form.html', {'form': form, 'title': 'Yangi guruh'})


@teacher_required
def group_edit(request, pk):
    group = get_object_or_404(Group, pk=pk)
    
    if not request.user.is_admin_role and group.teacher.user != request.user:
        messages.error(request, "Faqat o'zingizning guruhlaringizni tahrirlashingiz mumkin!")
        return redirect('courses:group_list')
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Guruh yangilandi!')
            return redirect('courses:group_list')
    else:
        form = GroupForm(instance=group)
    return render(request, 'courses/group_form.html', {'form': form, 'title': 'Guruhni tahrirlash', 'obj': group})


@teacher_required
def group_delete(request, pk):
    group = get_object_or_404(Group, pk=pk)
    
    if not request.user.is_admin_role and group.teacher.user != request.user:
        messages.error(request, "Faqat o'zingizning guruhlaringizni o'chirishingiz mumkin!")
        return redirect('courses:group_list')
    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Guruh o\'chirildi!')
        return redirect('courses:group_list')
    return render(request, 'courses/confirm_delete.html', {'obj': group, 'title': 'Guruhni o\'chirish'})


# ──────────── ENROLLMENTS ────────────
@teacher_required
def enrollment_create(request, group_pk):
    group = get_object_or_404(Group, pk=group_pk)
    
    if not request.user.is_admin_role and group.teacher.user != request.user:
        messages.error(request, "Faqat o'zingizning guruhlaringizga o'quvchi qo'shishingiz mumkin!")
        return redirect('courses:group_list')
    if request.method == 'POST':
        form = EnrollmentForm(request.POST, group=group)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.group = group
            enrollment.save()
            messages.success(request, f"{enrollment.student} guruhga qo'shildi!")
            return redirect('courses:group_detail', pk=group_pk)
    else:
        form = EnrollmentForm(group=group)
    return render(request, 'courses/enrollment_form.html', {'form': form, 'group': group})


@teacher_required
def enrollment_remove(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    group_pk = enrollment.group.pk
    
    if not request.user.is_admin_role and enrollment.group.teacher.user != request.user:
        messages.error(request, "Faqat o'zingizning guruhlaringizdan o'quvchi chiqarishingiz mumkin!")
        return redirect('courses:group_detail', pk=group_pk)
    if request.method == 'POST':
        enrollment.is_active = False
        enrollment.save()
        messages.success(request, "O'quvchi guruhdan chiqarildi!")
    return redirect('courses:group_detail', pk=group_pk)


@login_required
def group_export_excel(request, pk):
    group = get_object_or_404(Group, pk=pk)
    enrollments = group.enrollments.filter(is_active=True).select_related('student')
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = group.name
    ws.append(["#", "Ism", "Familiya", "Telefon", "Chegirma (%)", "Qo'shilgan sana"])
    for i, e in enumerate(enrollments, 1):
        ws.append([i, e.student.first_name, e.student.last_name, e.student.phone, e.discount_percent, str(e.enrolled_at)])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=group_{group.name}.xlsx'
    wb.save(response)
    return response
