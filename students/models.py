from django.db import models


from django.conf import settings

class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
        related_name='student_profile', null=True, blank=True,
        verbose_name='Foydalanuvchi'
    )
    class Gender(models.TextChoices):
        MALE = 'male', 'Erkak'
        FEMALE = 'female', 'Ayol'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Faol'
        INACTIVE = 'inactive', 'Faol emas'
        GRADUATED = 'graduated', 'Bitirgan'

    first_name = models.CharField(max_length=100, verbose_name='Ism')
    last_name = models.CharField(max_length=100, verbose_name='Familiya')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Otasining ismi')
    phone = models.CharField(max_length=20, verbose_name='Telefon')
    parent_phone = models.CharField(max_length=20, blank=True, verbose_name='Ota-ona telefoni')
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MALE, verbose_name='Jins')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Tug\'ilgan sana')
    address = models.TextField(blank=True, verbose_name='Manzil')
    photo = models.ImageField(upload_to='students/', blank=True, null=True, verbose_name='Rasm')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name='Holat')
    registered_at = models.DateField(auto_now_add=True, verbose_name='Ro\'yxatdan o\'tgan sana')
    notes = models.TextField(blank=True, verbose_name='Izoh')

    class Meta:
        verbose_name = "O'quvchi"
        verbose_name_plural = "O'quvchilar"
        ordering = ['-registered_at', 'last_name']

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    def get_full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()

    @property
    def active_enrollments(self):
        return self.enrollments.filter(is_active=True).select_related('group__course', 'group__teacher')

    @property
    def total_debt(self):
        from payments.models import Payment
        from django.db.models import Sum
        paid = Payment.objects.filter(student=self, status__in=['paid', 'partial']) \
                              .aggregate(total=Sum('amount'))['total'] or 0
        # calculate expected = sum of monthly fees
        expected = sum(
            e.group.course.monthly_fee
            for e in self.enrollments.filter(is_active=True).select_related('group__course')
        )
        return max(0, expected - paid)
