from django import forms
from .models import Course, Group, Enrollment
from teachers.models import Teacher


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description', 'duration_months', 'monthly_fee', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'duration_months': forms.NumberInput(attrs={'class': 'form-control'}),
            'monthly_fee': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# class CourseTeacherForm(forms.ModelForm):
#     class Meta:
#         model = CourseTeacher
#         fields = ['course', 'teacher', 'salary_type', 'salary_monthly', 'salary_percentage']
#         widgets = {
#             'course': forms.Select(attrs={'class': 'form-select'}),
#             'teacher': forms.Select(attrs={'class': 'form-select'}),
#             'salary_type': forms.Select(attrs={'class': 'form-select'}),
#             'salary_monthly': forms.NumberInput(attrs={'class': 'form-control'}),
#             'salary_percentage': forms.NumberInput(attrs={'class': 'form-control'}),
#         }


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'course', 'start_time', 'end_time', 'days', 'start_date', 'end_date', 'max_students', 'room', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'days': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'max_students': forms.NumberInput(attrs={'class': 'form-control'}),
            'room': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        active_teachers = Teacher.objects.filter(status='active').order_by('last_name', 'first_name')
        # Fallback: if no active teachers exist, show all to avoid empty select
        self.fields['teacher'].queryset = active_teachers if active_teachers.exists() else Teacher.objects.order_by(
            'last_name', 'first_name'
        )


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'discount_percent', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'discount_percent': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)
        from students.models import Student
        students = Student.objects.filter(status='active')
        if group is not None:
            enrolled_ids = group.enrollments.values_list('student_id', flat=True)
            students = students.exclude(id__in=enrolled_ids)
        self.fields['student'].queryset = students.order_by('last_name')
