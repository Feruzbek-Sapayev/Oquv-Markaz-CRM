from django.db import models


class Course(models.Model):
    name = models.CharField(max_length=200, verbose_name='Kurs nomi')
    description = models.TextField(blank=True, verbose_name='Tavsif')
    duration_months = models.PositiveIntegerField(default=6, verbose_name='Davomiyligi (oy)')
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Oylik to\'lov (so\'m)')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Kurs'
        verbose_name_plural = 'Kurslar'
        ordering = ['name']

    def __str__(self):
        return self.name


class Group(models.Model):
    class DayChoices(models.TextChoices):
        ODD = 'odd', 'Toq kunlar (Du, Ch, Ju)'
        EVEN = 'even', 'Juft kunlar (Se, Pa, Sha)'
        DAILY = 'daily', 'Har kuni'
        WEEKEND = 'weekend', 'Dam olish kunlari'

    name = models.CharField(max_length=100, verbose_name='Guruh nomi')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='groups', verbose_name='Kurs')
    teacher = models.ForeignKey(
        'teachers.Teacher', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='teaching_groups', verbose_name="O'qituvchi"
    )
    start_time = models.TimeField(verbose_name='Boshlanish vaqti')
    end_time = models.TimeField(verbose_name='Tugash vaqti')
    days = models.CharField(max_length=20, choices=DayChoices.choices, default=DayChoices.ODD, verbose_name='Dars kunlari')
    start_date = models.DateField(verbose_name='Boshlash sanasi')
    end_date = models.DateField(null=True, blank=True, verbose_name='Tugash sanasi')
    max_students = models.PositiveIntegerField(default=15, verbose_name='Max o\'quvchi soni')
    room = models.CharField(max_length=50, blank=True, verbose_name='Xona')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Guruh'
        verbose_name_plural = 'Guruhlar'
        ordering = ['-is_active', 'name']

    def __str__(self):
        return f"{self.name} ({self.course.name})"

    @property
    def student_count(self):
        return self.enrollments.filter(is_active=True).count()


class Enrollment(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='enrollments', verbose_name="O'quvchi")
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='enrollments', verbose_name='Guruh')
    enrolled_at = models.DateField(auto_now_add=True, verbose_name='Qo\'shilgan sana')
    left_at = models.DateField(null=True, blank=True, verbose_name='Ketgan sana')
    is_active = models.BooleanField(default=True, verbose_name='Faol')
    discount_percent = models.PositiveIntegerField(default=0, verbose_name='Chegirma (%)')
    notes = models.TextField(blank=True, verbose_name='Izoh')

    class Meta:
        verbose_name = "Ro'yxat"
        verbose_name_plural = "Ro'yxatlar"
        unique_together = ['student', 'group']
        ordering = ['-enrolled_at']

    def __str__(self):
        return f"{self.student} → {self.group}"

    @property
    def discounted_fee(self):
        original = self.group.course.monthly_fee
        discount = original * self.discount_percent / 100
        return original - discount
