from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date

class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        null=True,
        blank=True
    )
    admission_number = models.CharField(max_length=30, unique=True, help_text="e.g. ARF-2026-001")
    roll_number = models.CharField(max_length=15, blank=True)
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=15, default='Female', choices=[('Female', 'Female'), ('Male', 'Male')])
    blood_group = models.CharField(max_length=10, blank=True)
    current_class = models.ForeignKey(
        'academics.SchoolClass',
        on_delete=models.PROTECT,
        related_name='students'
    )
    academic_year = models.ForeignKey(
        'academics.AcademicYear',
        on_delete=models.PROTECT,
        related_name='enrolled_students'
    )
    father_or_guardian_name = models.CharField(max_length=150)
    mother_name = models.CharField(max_length=150, blank=True)
    guardian_phone = models.CharField(max_length=20)
    guardian_email = models.EmailField(blank=True)
    guardian_occupation = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to='students/photos/', blank=True, null=True)
    admission_date = models.DateField(default=timezone.now)
    vehicle_opted = models.BooleanField(default=False, help_text="Opted for academy bus/transportation")
    vehicle_route = models.CharField(max_length=100, blank=True, help_text="e.g. Kodampuzha Route, Feroke Route, Ramanattukara Route")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['current_class', 'roll_number', 'full_name']

    def __str__(self):
        return f"{self.full_name} ({self.admission_number} - {self.current_class.display_name})"

    def get_today_attendance(self):
        from attendance.models import StudentAttendanceRecord
        today = date.today()
        record = StudentAttendanceRecord.objects.filter(student=self, session__date=today).first()
        return record.status if record else 'NOT_MARKED'

    def get_monthly_attendance_stats(self, year=None, month=None):
        from attendance.models import StudentAttendanceRecord
        today = date.today()
        year = year or today.year
        month = month or today.month

        records = StudentAttendanceRecord.objects.filter(
            student=self,
            session__date__year=year,
            session__date__month=month
        )
        total_days = records.count()
        present_days = records.filter(status='PRESENT').count()
        absent_days = records.filter(status='ABSENT').count()
        late_days = records.filter(status='LATE').count()
        excused_days = records.filter(status='EXCUSED').count()

        pct = round((present_days / total_days * 100), 1) if total_days > 0 else 0.0
        return {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'excused_days': excused_days,
            'percentage': pct,
            'month': month,
            'year': year
        }

    def get_yearly_attendance_stats(self):
        from attendance.models import StudentAttendanceRecord
        records = StudentAttendanceRecord.objects.filter(
            student=self,
            session__school_class__academic_year=self.academic_year
        )
        total_days = records.count()
        present_days = records.filter(status='PRESENT').count()
        absent_days = records.filter(status='ABSENT').count()
        late_days = records.filter(status='LATE').count()
        pct = round((present_days / total_days * 100), 1) if total_days > 0 else 0.0
        return {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'percentage': pct
        }
