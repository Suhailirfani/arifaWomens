from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from decimal import Decimal

from .models import Exam, ExamSchedule, StudentMark
from .pdf_utils import generate_progress_report_pdf
from academics.models import SchoolClass, AcademicYear
from students.models import Student

@login_required
def exam_list(request):
    exams = Exam.objects.select_related('academic_year').prefetch_related('schedules__school_class', 'schedules__subject').order_by('-start_date')
    return render(request, 'examinations/exam_list.html', {'exams': exams})


@login_required
def marks_entry(request):
    """
    Teacher & Admin marks entry screen for a specific Exam Schedule.
    """
    schedules = ExamSchedule.objects.select_related('exam', 'school_class__grade', 'school_class__course', 'subject').order_by('-exam__start_date', 'school_class', 'subject')
    
    selected_sched_id = request.GET.get('schedule_id') or request.POST.get('schedule_id')
    selected_schedule = None
    if selected_sched_id:
        selected_schedule = ExamSchedule.objects.filter(id=selected_sched_id).first()
    if not selected_schedule and schedules.exists():
        selected_schedule = schedules.first()

    students = []
    marks_map = {}
    if selected_schedule:
        students = selected_schedule.school_class.students.filter(is_active=True).order_by('roll_number', 'full_name')
        existing_marks = StudentMark.objects.filter(exam_schedule=selected_schedule)
        marks_map = {m.student_id: m for m in existing_marks}

    if request.method == 'POST' and selected_schedule:
        saved_count = 0
        for s in students:
            val_str = request.POST.get(f'marks_{s.id}', '').strip()
            is_absent = request.POST.get(f'absent_{s.id}') == 'on'
            remarks = request.POST.get(f'remarks_{s.id}', '').strip()

            marks_val = None
            if not is_absent and val_str:
                try:
                    marks_val = Decimal(val_str)
                except Exception:
                    marks_val = None

            StudentMark.objects.update_or_create(
                exam_schedule=selected_schedule,
                student=s,
                defaults={
                    'marks_obtained': marks_val,
                    'is_absent': is_absent,
                    'remarks': remarks
                }
            )
            saved_count += 1

        messages.success(request, f"Marks updated successfully for {saved_count} students in {selected_schedule.subject.name} ({selected_schedule.school_class.display_name}).")
        return redirect(f"/examinations/marks/entry/?schedule_id={selected_schedule.id}")

    student_entries = []
    for s in students:
        m_obj = marks_map.get(s.id)
        student_entries.append({
            'student': s,
            'mark_obj': m_obj,
            'marks_val': m_obj.marks_obtained if m_obj else '',
            'is_absent': m_obj.is_absent if m_obj else False,
            'remarks': m_obj.remarks if m_obj else ''
        })

    context = {
        'schedules': schedules,
        'selected_schedule': selected_schedule,
        'student_entries': student_entries,
    }
    return render(request, 'examinations/marks_entry.html', context)


@login_required
def progress_report(request, student_id, exam_id):
    """
    HTML view of student's progress report card for an examination.
    """
    student = get_object_or_404(Student.objects.select_related('current_class__grade', 'current_class__course', 'academic_year'), pk=student_id)
    exam = get_object_or_404(Exam, pk=exam_id)

    marks_records = StudentMark.objects.filter(
        student=student,
        exam_schedule__exam=exam
    ).select_related('exam_schedule__subject').order_by('exam_schedule__subject__name')

    total_max = sum(float(m.exam_schedule.max_marks) for m in marks_records)
    total_obtained = sum(float(m.marks_obtained or 0) for m in marks_records if not m.is_absent)
    percentage = round((total_obtained / total_max * 100), 1) if total_max else 0.0

    monthly_stats = student.get_monthly_attendance_stats()

    context = {
        'student': student,
        'exam': exam,
        'marks_records': marks_records,
        'total_max': total_max,
        'total_obtained': total_obtained,
        'percentage': percentage,
        'monthly_stats': monthly_stats,
    }
    return render(request, 'examinations/progress_report.html', context)


@login_required
def download_progress_report_pdf(request, student_id, exam_id):
    """
    Generates and downloads student progress report card as a PDF.
    """
    student = get_object_or_404(Student.objects.select_related('current_class__grade', 'current_class__course', 'academic_year'), pk=student_id)
    exam = get_object_or_404(Exam, pk=exam_id)

    marks_records = StudentMark.objects.filter(
        student=student,
        exam_schedule__exam=exam
    ).select_related('exam_schedule__subject').order_by('exam_schedule__subject__name')

    pdf_bytes = generate_progress_report_pdf(student, exam, marks_records)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    sanitized_name = student.full_name.replace(' ', '_')
    response['Content-Disposition'] = f'attachment; filename="ReportCard_{sanitized_name}_{exam.id}.pdf"'
    return response
