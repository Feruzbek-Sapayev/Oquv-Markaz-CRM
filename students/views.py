from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Student
from .forms import StudentForm
from accounts.permissions import admin_required, teacher_required
from courses.models import Enrollment, Group
import openpyxl
from django.http import HttpResponse


@login_required
def student_list(request):
    if request.user.is_admin_role:
        students = Student.objects.all()
    elif request.user.is_teacher:
        students = Student.objects.filter(enrollments__group__teacher__user=request.user).distinct()
    else:
        messages.error(request, "Sizda o'quvchilar ro'yxatini ko'rish huquqi yo'q!")
        return redirect('dashboard:home')

    query = request.GET.get('q', '')
    status = request.GET.get('status', '')
    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone__icontains=query)
        )
    if status:
        students = students.filter(status=status)

    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'students': page_obj,
        'page_obj': page_obj,
        'query': query,
        'status': status,
        'statuses': Student.Status.choices,
    }
    return render(request, 'students/student_list.html', context)


@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    # Permission check
    if not request.user.is_admin_role:
        if request.user.is_teacher:
            if not student.enrollments.filter(group__teacher__user=request.user).exists():
                messages.error(request, "Ushbu o'quvchi ma'lumotlarini ko'rish huquqingiz yo'q!")
                return redirect('students:list')
        elif request.user.is_student:
            if student.user != request.user:
                messages.error(request, "Faqat o'z ma'lumotlaringizni ko'rishingiz mumkin!")
                return redirect('dashboard:home')
        else:
            return redirect('dashboard:home')

    enrollments = student.enrollments.select_related('group__course', 'group__teacher').order_by('-enrolled_at')
    payments = student.payments.select_related('group__course').order_by('-year', '-month')
    attendances = student.attendances.select_related('session__group').order_by('-session__date')[:20]
    context = {
        'student': student,
        'enrollments': enrollments,
        'payments': payments,
        'attendances': attendances,
    }
    return render(request, 'students/student_detail.html', context)


@admin_required
def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            messages.success(request, f"{student} muvaffaqiyatli qo'shildi!")
            return redirect('students:detail', pk=student.pk)
    else:
        form = StudentForm()
    return render(request, 'students/student_form.html', {'form': form, 'title': "Yangi o'quvchi"})


@admin_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "O'quvchi ma'lumotlari yangilandi!")
            return redirect('students:detail', pk=pk)
    else:
        form = StudentForm(instance=student)
    return render(request, 'students/student_form.html', {'form': form, 'title': "Tahrirlash", 'obj': student})


@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if not request.user.is_admin_role:
        messages.error(request, "Ruxsatingiz yo'q!")
        return redirect('students:list')
    if request.method == 'POST':
        student.delete()
        messages.success(request, "O'quvchi o'chirildi!")
        return redirect('students:list')
    return render(request, 'students/student_confirm_delete.html', {'obj': student})


@admin_required
def student_export_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "O'quvchilar"
    headers = ["#", "Ism", "Familiya", "Telefon", "Jins", "Holat", "Ro'yxat sanasi"]
    ws.append(headers)
    for i, s in enumerate(Student.objects.all(), 1):
        ws.append([i, s.first_name, s.last_name, s.phone, s.get_gender_display(), s.get_status_display(), str(s.registered_at)])
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = "attachment; filename=students.xlsx"
    wb.save(response)
    return response
