from django.db import models

class AcademicYear(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="e.g. 2026-2027")
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.filter(is_current=True).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}{' (Current)' if self.is_current else ''}"


class GradeLevel(models.Model):
    class LevelCategory(models.TextChoices):
        HIGH_SCHOOL = 'high_school', 'High School'
        HIGHER_SECONDARY = 'higher_secondary', 'Higher Secondary'

    name = models.CharField(max_length=50, help_text="e.g. Class 8, Class 9, Class 10, Plus One, Plus Two")
    level_category = models.CharField(max_length=30, choices=LevelCategory.choices, default=LevelCategory.HIGHER_SECONDARY)
    sequence = models.PositiveIntegerField(default=1, help_text="Sort order")

    class Meta:
        ordering = ['sequence', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_level_category_display()})"


class Course(models.Model):
    name = models.CharField(max_length=100, help_text="e.g. Humanities, Commerce, Science, General")
    code = models.CharField(max_length=20, unique=True, help_text="e.g. HUM, COM, SCI, GEN")
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class SchoolClass(models.Model):
    """
    A class is the combination of Grade and Course (e.g. Plus One Humanities, Plus One Commerce, Class 10 General).
    """
    grade = models.ForeignKey(GradeLevel, on_delete=models.CASCADE, related_name='classes')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='classes')
    section = models.CharField(max_length=10, default='A', help_text="e.g. A, B, C")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='classes')
    class_teacher = models.ForeignKey(
        'staff.StaffProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_classes'
    )
    room_number = models.CharField(max_length=30, blank=True)

    class Meta:
        verbose_name_plural = 'School Classes'
        unique_together = ('grade', 'course', 'section', 'academic_year')
        ordering = ['grade__sequence', 'course__name', 'section']

    @property
    def display_name(self):
        if self.course.name.lower() == 'general':
            return f"{self.grade.name} - Section {self.section}"
        return f"{self.grade.name} {self.course.name} - Section {self.section}"

    def __str__(self):
        return f"{self.display_name} ({self.academic_year.name})"


class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    school_classes = models.ManyToManyField(SchoolClass, related_name='subjects', blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"
