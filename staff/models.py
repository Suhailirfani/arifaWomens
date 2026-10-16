from django.db import models
from django.conf import settings

class StaffProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='staff_profile',
        null=True,
        blank=True
    )
    staff_id = models.CharField(max_length=30, unique=True, help_text="e.g. ARF-STF-01")
    full_name = models.CharField(max_length=150)
    gender = models.CharField(max_length=15, default='Female', choices=[('Female', 'Female'), ('Male', 'Male'), ('Other', 'Other')])
    designation = models.CharField(max_length=100, help_text="e.g. Senior Lecturer, Teacher, Office Superintendent, Accountant")
    department = models.CharField(max_length=100, blank=True, help_text="e.g. Humanities, Commerce, Science, Administration")
    qualification = models.CharField(max_length=150, blank=True, help_text="e.g. M.A. English, B.Ed, M.Com")
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    joining_date = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='staff/photos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    subjects_taught = models.ManyToManyField('academics.Subject', blank=True, related_name='teachers')

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return f"{self.full_name} ({self.designation} - {self.staff_id})"
