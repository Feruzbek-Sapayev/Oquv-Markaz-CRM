from django.db import models


from django.conf import settings

class Teacher(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
        related_name='teacher_profile', null=True, blank=True,
        verbose_name='Foydalanuvchi'
    )
    class Gender(models.TextChoices):
        MALE = 'male', 'Erkak'
        FEMALE = 'female', 'Ayol'

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Faol'
        INACTIVE = 'inactive', 'Faol emas'

    first_name = models.CharField(max_length=100, verbose_name='Ism')
    last_name = models.CharField(max_length=100, verbose_name='Familiya')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Otasining ismi')
    phone = models.CharField(max_length=20, verbose_name='Telefon')
    email = models.EmailField(blank=True, verbose_name='Email')
    gender = models.CharField(max_length=10, choices=Gender.choices, default=Gender.MALE, verbose_name='Jins')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Tug\'ilgan sana')
    address = models.TextField(blank=True, verbose_name='Manzil')
    photo = models.ImageField(upload_to='teachers/', blank=True, null=True, verbose_name='Rasm')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, verbose_name='Holat')
    hired_at = models.DateField(null=True, blank=True, verbose_name='Ishga kirgan sana')
    salary_monthly = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Oylik maosh')
    notes = models.TextField(blank=True, verbose_name='Izoh')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "O'qituvchi"
        verbose_name_plural = "O'qituvchilar"
        ordering = ['-created_at', 'last_name']

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name}".strip()
