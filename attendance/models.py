from django.db import models
from django.utils import timezone

class DailyAttendanceSession(models.Model):
    school_class = models.ForeignKey(
        'academics.SchoolClass',
        on_delete=models.CASCADE,
        related_name='attendance_sessions'
    )
    date = models.DateField(default=timezone.now)
    taken_by = models.ForeignKey(
        'staff.StaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taken_attendances'
    )
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('school_class', 'date')
        ordering = ['-date', 'school_class']

    def __str__(self):
        return f"{self.school_class.display_name} - {self.date}"

    @property
    def total_students(self):
        return self.records.count()

    @property
    def present_count(self):
        return self.records.filter(status='PRESENT').count()

    @property
    def absent_count(self):
        return self.records.filter(status='ABSENT').count()

    @property
    def late_count(self):
        return self.records.filter(status='LATE').count()

    @property
    def attendance_rate(self):
        total = self.total_students
        if total == 0:
            return 0.0
        return round((self.present_count / total) * 100, 1)


class StudentAttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Present'
        ABSENT = 'ABSENT', 'Absent'
        LATE = 'LATE', 'Late'
        EXCUSED = 'EXCUSED', 'Excused / Leave'

    session = models.ForeignKey(
        DailyAttendanceSession,
        on_delete=models.CASCADE,
        related_name='records'
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PRESENT
    )
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ('session', 'student')
        ordering = ['student__roll_number', 'student__full_name']

    def __str__(self):
        return f"{self.student.full_name} - {self.session.date}: {self.get_status_display()}"
