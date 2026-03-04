from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum, Count, Q
from django.utils import timezone
from students.models import Student
from courses.models import Course, Group, Enrollment
from payments.models import Payment
from attendance.models import Attendance


@login_required
def home(request):
    User = get_user_model()
    now = timezone.now()
    month = now.month
    year = now.year

    total_students = Student.objects.count()
    total_groups = Group.objects.filter(is_active=True).count()
    total_teachers = User.objects.filter(role='teacher').count()
    
    monthly_income = Payment.objects.filter(
        month=month, year=year, status__in=['paid', 'partial']
    ).aggregate(total=Sum('amount'))['total'] or 0

    debtor_count = Payment.objects.filter(
        month=month, year=year, status__in=['unpaid', 'partial']
    ).values('student').distinct().count()

    total_debt = Payment.objects.filter(
        status__in=['unpaid', 'partial']
    ).aggregate(
        debt=Sum('expected_amount') - Sum('amount')
    )['debt'] or 0

    recent_payments = Payment.objects.select_related(
        'student', 'group__course', 'created_by'
    ).order_by('-created_at')[:8]

    recent_students = Student.objects.order_by('-registered_at')[:6]

    # Monthly income chart data (last 6 months)
    chart_months = []
    chart_income = []
    for i in range(5, -1, -1):
        m = month - i
        y = year
        if m <= 0:
            m += 12
            y -= 1
        income = Payment.objects.filter(
            month=m, year=y, status__in=['paid', 'partial']
        ).aggregate(total=Sum('amount'))['total'] or 0
        chart_months.append(f"{m:02d}/{y}")
        chart_income.append(float(income))

    groups_with_counts = Group.objects.filter(is_active=True).select_related('course', 'teacher').annotate(
        enrolled=Count('enrollments', filter=Q(enrollments__is_active=True))
    )[:5]

    context = {
        'total_students': total_students,
        'total_groups': total_groups,
        'total_teachers': total_teachers,
        'monthly_income': monthly_income,
        'debtor_count': debtor_count,
        'total_debt': total_debt,
        'recent_payments': recent_payments,
        'recent_students': recent_students,
        'chart_months': chart_months,
        'chart_income': chart_income,
        'groups_with_counts': groups_with_counts,
        'now': now,
    }
    return render(request, 'dashboard/home.html', context)
