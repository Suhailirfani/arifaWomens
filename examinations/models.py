from django.db import models
from decimal import Decimal

class Exam(models.Model):
    name = models.CharField(max_length=150, help_text="e.g. First Terminal Examination, Mid-Term Examination, Model Exam")
    academic_year = models.ForeignKey(
        'academics.AcademicYear',
        on_delete=models.CASCADE,
        related_name='exams'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.name} ({self.academic_year.name})"


class ExamSchedule(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='schedules')
    school_class = models.ForeignKey('academics.SchoolClass', on_delete=models.CASCADE, related_name='exam_schedules')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='exam_schedules')
    exam_date = models.DateField()
    max_marks = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.00'))
    pass_marks = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('35.00'))

    class Meta:
        unique_together = ('exam', 'school_class', 'subject')
        ordering = ['exam_date', 'subject__name']

    def __str__(self):
        return f"{self.exam.name} - {self.school_class.display_name} - {self.subject.name}"


class StudentMark(models.Model):
    exam_schedule = models.ForeignKey(ExamSchedule, on_delete=models.CASCADE, related_name='student_marks')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='exam_marks')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_absent = models.BooleanField(default=False)
    remarks = models.CharField(max_length=150, blank=True)

    class Meta:
        unique_together = ('exam_schedule', 'student')
        ordering = ['student__roll_number', 'student__full_name']

    def __str__(self):
        return f"{self.student.full_name} - {self.exam_schedule.subject.name}: {self.marks_obtained if not self.is_absent else 'Absent'}"

    @property
    def percentage(self):
        if self.is_absent or self.marks_obtained is None:
            return 0.0
        max_m = float(self.exam_schedule.max_marks)
        if max_m <= 0:
            return 0.0
        return round((float(self.marks_obtained) / max_m) * 100, 1)

    @property
    def letter_grade(self):
        if self.is_absent:
            return 'ABS'
        if self.marks_obtained is None:
            return '-'
        pct = self.percentage
        if pct >= 90:
            return 'A+'
        elif pct >= 80:
            return 'A'
        elif pct >= 70:
            return 'B+'
        elif pct >= 60:
            return 'B'
        elif pct >= 50:
            return 'C+'
        elif pct >= 40:
            return 'C'
        elif pct >= 35:
            return 'D+'
        else:
            return 'E (Needs Improvement)'
