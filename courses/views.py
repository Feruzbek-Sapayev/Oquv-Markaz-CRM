from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Course, Group, Enrollment, CourseTeacher
from .forms import CourseForm, GroupForm, EnrollmentForm, CourseTeacherForm
from accounts.permissions import admin_required, teacher_required
import openpyxl
from django.http import HttpResponse


# ──────────── COURSES ────────────
@login_required
def course_list(request):
    courses = Course.objects.all()
    return render(request, 'courses/course_list.html', {'courses': courses})

@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    teachers = course.course_teachers.select_related('teacher').all()
    groups = course.groups.all()
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'teachers': teachers,
        'groups': groups
    })

@admin_required
def course_assign_teacher(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseTeacherForm(request.POST)
        if form.is_valid():
            ct = form.save(commit=False)
            ct.course = course
            ct.save()
            messages.success(request, f"{ct.teacher} kursga biriktirildi!")
            return redirect('courses:course_detail', pk=pk)
    else:
        form = CourseTeacherForm()
    return render(request, 'courses/course_teacher_form.html', {'form': form, 'course': course, 'title': "O'qituvchi biriktirish"})

@admin_required
def course_remove_teacher(request, pk):
    ct = get_object_or_404(CourseTeacher, pk=pk)
    course_pk = ct.course.pk
    if request.method == 'POST':
        ct.delete()
        messages.success(request, "O'qituvchi kursdan olib tashlandi!")
    return redirect('courses:course_detail', pk=course_pk)

@admin_required
def course_create(request):
    CourseTeacherFormSet = inlineformset_factory(
        Course, CourseTeacher, 
        form=CourseTeacherForm,
        extra=1, can_delete=True
    )
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES)
        formset = CourseTeacherFormSet(request.POST, prefix='course_teachers')
        if form.is_valid() and formset.is_valid():
            course = form.save()
            instances = formset.save(commit=False)
            for instance in instances:
                instance.course = course
                instance.save()
            for obj in formset.deleted_objects:
                obj.delete()
            messages.success(request, f"'{course.name}' kursi va o'qituvchilari saqlandi!")
            return redirect('courses:course_detail', pk=course.pk)
    else:
        form = CourseForm()
        formset = CourseTeacherFormSet(prefix='course_teachers')
    return render(request, 'courses/course_form.html', {
        'form': form, 
        'formset': formset,
        'title': 'Yangi kurs'
    })

@admin_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    CourseTeacherFormSet = inlineformset_factory(
        Course, CourseTeacher, 
        form=CourseTeacherForm,
        extra=0, can_delete=True
    )
    if request.method == 'POST':
        form = CourseForm(request.POST, request.FILES, instance=course)
        formset = CourseTeacherFormSet(request.POST, instance=course, prefix='course_teachers')
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Kurs ma'lumotlari yangilandi!")
            return redirect('courses:course_detail', pk=pk)
    else:
        form = CourseForm(instance=course)
        formset = CourseTeacherFormSet(instance=course, prefix='course_teachers')
    return render(request, 'courses/course_form.html', {
        'form': form, 
        'formset': formset,
        'title': 'Tahrirlash', 
        'obj': course
    })


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
        groups = Group.objects.select_related('course').all()
    elif request.user.is_teacher:
        groups = Group.objects.filter(course__course_teachers__teacher__user=request.user).select_related('course').distinct()
    elif request.user.is_student:
        groups = Group.objects.filter(enrollments__student__user=request.user, enrollments__is_active=True).select_related('course').distinct()
    else:
        groups = Group.objects.none()

    paginator = Paginator(groups, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'courses/group_list.html', {'groups': page_obj, 'page_obj': page_obj})


@login_required
def group_detail(request, pk):
    group = get_object_or_404(Group.objects.select_related('course'), pk=pk)
    
    # Permission check
    if not request.user.is_admin_role:
        if request.user.is_teacher and not group.course.course_teachers.filter(teacher__user=request.user).exists():
            messages.error(request, "Bu guruhga kirish huquqingiz yo'q!")
            return redirect('courses:group_list')
        if request.user.is_student and not group.enrollments.filter(student__user=request.user, is_active=True).exists():
            messages.error(request, "Siz ushbu guruhga a'zo emassiz!")
            return redirect('courses:group_list')

    enrollments = group.enrollments.filter(is_active=True).select_related('student')
    teachers = group.course.course_teachers.select_related('teacher')
    return render(request, 'courses/group_detail.html', {
        'group': group,
        'enrollments': enrollments,
        'teachers': teachers,
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
    
    if not request.user.is_admin_role and not group.course.course_teachers.filter(teacher__user=request.user).exists():
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
    
    if not request.user.is_admin_role and not group.course.course_teachers.filter(teacher__user=request.user).exists():
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
    
    if not request.user.is_admin_role and not group.course.course_teachers.filter(teacher__user=request.user).exists():
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
    
    if not request.user.is_admin_role and not enrollment.group.course.course_teachers.filter(teacher__user=request.user).exists():
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
@login_required
def lesson_schedule(request):
    # Determine which groups to show based on role
    if request.user.is_admin_role:
        groups = Group.objects.filter(is_active=True).select_related('course')
    elif request.user.is_teacher:
        groups = Group.objects.filter(
            is_active=True,
            course__course_teachers__teacher__user=request.user
        ).select_related('course').distinct()
    elif request.user.is_student:
        groups = Group.objects.filter(
            is_active=True,
            enrollments__student__user=request.user,
            enrollments__is_active=True
        ).select_related('course').distinct()
    else:
        groups = Group.objects.none()
    
    # Organize groups by day
    # We'll use day names in Uzbek for the frontend
    days_map = [
        ('Monday', 'Dushanba'),
        ('Tuesday', 'Seshanba'),
        ('Wednesday', 'Chorshanba'),
        ('Thursday', 'Payshanba'),
        ('Friday', 'Juma'),
        ('Saturday', 'Shanba'),
        ('Sunday', 'Yakshanba'),
    ]
    
    schedule = {day[1]: [] for day in days_map}
    
    for group in groups:
        if group.days == Group.DayChoices.ODD:
            schedule['Dushanba'].append(group)
            schedule['Chorshanba'].append(group)
            schedule['Juma'].append(group)
        elif group.days == Group.DayChoices.EVEN:
            schedule['Seshanba'].append(group)
            schedule['Payshanba'].append(group)
            schedule['Shanba'].append(group)
        elif group.days == Group.DayChoices.DAILY:
            for day in schedule:
                schedule[day].append(group)
        elif group.days == Group.DayChoices.WEEKEND:
            schedule['Shanba'].append(group)
            schedule['Yakshanba'].append(group)
            
    # Sort each day by start_time
    for day in schedule:
        schedule[day].sort(key=lambda x: x.start_time)
        
    return render(request, 'courses/schedule.html', {'schedule': schedule, 'title': 'Dars Jadvali'})
