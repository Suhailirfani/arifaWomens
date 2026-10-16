from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        OFFICE_STAFF = 'office_staff', 'Office Staff'
        TEACHER = 'teacher', 'Teacher'
        PARENT = 'parent', 'Parent / Student'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN,
        help_text="Designates the user's operational role across portals."
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    @property
    def is_administrator(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    @property
    def is_office_staff(self):
        return self.role == self.Role.OFFICE_STAFF

    @property
    def is_teacher_user(self):
        return self.role == self.Role.TEACHER

    @property
    def is_parent_user(self):
        return self.role == self.Role.PARENT

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
