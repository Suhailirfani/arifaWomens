from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import date, timedelta

from .models import Student
from .forms import StudentForm, BulkUploadForm
from .excel_utils import generate_student_excel_template, parse_student_bulk_excel
from academics.models import SchoolClass, AcademicYear
from attendance.models import StudentAttendanceRecord
from fees.models import StudentFeePayment, FeeInstallment
from examinations.models import StudentMark, Exam

@login_required
def student_list(request):
    query = request.GET.get('q', '').strip()
    class_id = request.GET.get('class_id', '').strip()
    status_filter = request.GET.get('status', 'active')

    students = Student.objects.select_related('current_class__grade', 'current_class__course', 'academic_year')

    if status_filter == 'active':
        students = students.filter(is_active=True)
    elif status_filter == 'inactive':
        students = students.filter(is_active=False)

    if class_id:
        students = students.filter(current_class_id=class_id)

    if query:
        students = students.filter(
            Q(full_name__icontains=query) |
            Q(admission_number__icontains=query) |
            Q(roll_number__icontains=query) |
            Q(guardian_phone__icontains=query) |
            Q(father_or_guardian_name__icontains=query)
        )

    school_classes = SchoolClass.objects.all()

    paginator = Paginator(students, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'school_classes': school_classes,
        'query': query,
        'class_id': class_id,
        'status_filter': status_filter,
        'total_count': students.count()
    }
    return render(request, 'students/student_list.html', context)


@login_required
def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()
            messages.success(request, f"Student '{student.full_name}' ({student.admission_number}) registered successfully!")
            return redirect('students:student_profile', student_id=student.id)
    else:
        # Default academic year
        cur_ay = AcademicYear.objects.filter(is_current=True).first()
        form = StudentForm(initial={'academic_year': cur_ay})

    return render(request, 'students/student_form.html', {'form': form, 'title': 'Register New Student'})


@login_required
def student_edit(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student details for '{student.full_name}' updated successfully!")
            return redirect('students:student_profile', student_id=student.id)
    else:
        form = StudentForm(instance=student)

    return render(request, 'students/student_form.html', {'form': form, 'student': student, 'title': f'Edit Student: {student.full_name}'})


@login_required
def student_delete(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    if request.method == 'POST':
        name = student.full_name
        student.delete()
        messages.success(request, f"Student '{name}' has been deleted from records.")
        return redirect('students:student_list')
    return render(request, 'students/student_confirm_delete.html', {'student': student})


@login_required
def student_profile(request, student_id):
    """
    Student Profile with Attendance Calendar Heatmap (Green for present, Red for absent),
    fee payments, and examination marks.
    """
    student = get_object_or_404(
        Student.objects.select_related('current_class__grade', 'current_class__course', 'academic_year', 'current_class__class_teacher'),
        pk=student_id
    )

    # 1. Attendance Heatmap Generator (Past 12 weeks / 84 days)
    today = date.today()
    start_date = today - timedelta(days=83)
    
    # Align to previous Monday
    offset = start_date.weekday()
    cal_start = start_date - timedelta(days=offset)

    records_map = {
        r.session.date: r.status
        for r in StudentAttendanceRecord.objects.filter(student=student, session__date__gte=cal_start)
    }

    # Generate weeks list for GitHub/Bento style heatmap
    weeks = []
    cur = cal_start
    while cur <= today:
        week_days = []
        for _ in range(7):
            if cur > today:
                status = 'FUTURE'
            elif cur.weekday() == 6: # Sunday
                status = 'HOLIDAY'
            else:
                status = records_map.get(cur, 'NO_RECORD')
            
            week_days.append({
                'date': cur,
                'status': status,
                'day_num': cur.day,
                'is_today': cur == today
            })
            cur += timedelta(days=1)
        weeks.append(week_days)

    # Monthly & Yearly Attendance Stats
    monthly_stats = student.get_monthly_attendance_stats()
    yearly_stats = student.get_yearly_attendance_stats()

    # Fee payments & pending dues
    payments = student.fee_payments.select_related('installment__fee_structure').order_by('-payment_date')
    paid_installment_ids = payments.values_list('installment_id', flat=True)

    due_installments = FeeInstallment.objects.filter(
        Q(fee_structure__school_class=student.current_class) | Q(fee_structure__grade=student.current_class.grade)
    ).exclude(id__in=paid_installment_ids)
    if not student.vehicle_opted:
        due_installments = due_installments.filter(requires_vehicle=False)

    # Exam marks
    exams = Exam.objects.filter(academic_year=student.academic_year, is_published=True).order_by('-start_date')
    exam_results = []
    for ex in exams:
        marks = StudentMark.objects.filter(student=student, exam_schedule__exam=ex).select_related('exam_schedule__subject')
        if marks.exists():
            tot_obtained = sum(float(m.marks_obtained or 0) for m in marks if not m.is_absent)
            tot_max = sum(float(m.exam_schedule.max_marks) for m in marks)
            pct = round((tot_obtained / tot_max * 100), 1) if tot_max else 0
            exam_results.append({
                'exam': ex,
                'marks': marks,
                'tot_obtained': tot_obtained,
                'tot_max': tot_max,
                'pct': pct
            })

    context = {
        'student': student,
        'weeks': weeks,
        'today': today,
        'today_status': student.get_today_attendance(),
        'monthly_stats': monthly_stats,
        'yearly_stats': yearly_stats,
        'payments': payments,
        'due_installments': due_installments,
        'exam_results': exam_results,
    }
    return render(request, 'students/student_profile.html', context)


@login_required
def student_bulk_upload(request):
    """
    Bulk Excel upload: uploads .xlsx, parses rows, validates, and batch creates students.
    """
    if request.method == 'POST':
        form = BulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            try:
                created_count, updated_count, errors = parse_student_bulk_excel(excel_file)
                if created_count > 0 or updated_count > 0:
                    messages.success(request, f"Bulk upload completed: {created_count} students added, {updated_count} updated.")
                if errors:
                    for err in errors[:5]:
                        messages.warning(request, err)
                    if len(errors) > 5:
                        messages.warning(request, f"...and {len(errors) - 5} more row warnings.")
                return redirect('students:student_list')
            except Exception as e:
                messages.error(request, f"Error processing Excel file: {str(e)}")
    else:
        form = BulkUploadForm()

    return render(request, 'students/student_bulk_upload.html', {'form': form})


@login_required
def download_student_template(request):
    """
    Download empty or prefilled Excel template for bulk student registration.
    """
    excel_content = generate_student_excel_template()
    response = HttpResponse(
        excel_content,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="arifa_student_bulk_upload_template.xlsx"'
    return response
