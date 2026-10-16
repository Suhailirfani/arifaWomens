from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, Avg
from datetime import date
from decimal import Decimal

from academics.models import AcademicYear, SchoolClass, Subject
from staff.models import StaffProfile
from students.models import Student
from attendance.models import DailyAttendanceSession, StudentAttendanceRecord
from fees.models import FeeStructure, FeeInstallment, StudentFeePayment
from examinations.models import Exam, ExamSchedule, StudentMark

@login_required
def admin_dashboard(request):
    today = date.today()
    current_ay = AcademicYear.objects.filter(is_current=True).first()

    total_students = Student.objects.filter(is_active=True).count()
    total_staff = StaffProfile.objects.filter(is_active=True).count()
    total_classes = SchoolClass.objects.count()

    # Today's attendance calculation across academy
    today_sessions = DailyAttendanceSession.objects.filter(date=today)
    today_records = StudentAttendanceRecord.objects.filter(session__in=today_sessions)
    today_total = today_records.count()
    today_present = today_records.filter(status='PRESENT').count()
    today_absent = today_records.filter(status='ABSENT').count()
    today_rate = round((today_present / today_total * 100), 1) if today_total > 0 else 0.0

    # Class-wise attendance breakdown
    classes = SchoolClass.objects.select_related('grade', 'course', 'class_teacher').all()
    class_stats = []
    for sc in classes:
        session = today_sessions.filter(school_class=sc).first()
        sc_total = sc.students.filter(is_active=True).count()
        if session:
            sc_present = session.present_count
            sc_absent = session.absent_count
            sc_rate = session.attendance_rate
            is_taken = True
        else:
            sc_present = 0
            sc_absent = 0
            sc_rate = 0.0
            is_taken = False
        class_stats.append({
            'class': sc,
            'total': sc_total,
            'present': sc_present,
            'absent': sc_absent,
            'rate': sc_rate,
            'is_taken': is_taken
        })

    # Fee collections & active due installment
    current_due_inst = FeeInstallment.objects.filter(is_current_due=True).first()
    if not current_due_inst:
        current_due_inst = FeeInstallment.objects.order_by('due_date').first()

    paid_count = 0
    unpaid_count = 0
    total_collected_amount = Decimal('0.00')
    total_pending_amount = Decimal('0.00')

    if current_due_inst:
        # Determine eligible students
        eligible_qs = Student.objects.filter(is_active=True)
        if current_due_inst.fee_structure.school_class:
            eligible_qs = eligible_qs.filter(current_class=current_due_inst.fee_structure.school_class)
        elif current_due_inst.fee_structure.grade:
            eligible_qs = eligible_qs.filter(current_class__grade=current_due_inst.fee_structure.grade)

        if current_due_inst.requires_vehicle:
            eligible_qs = eligible_qs.filter(vehicle_opted=True)

        paid_student_ids = StudentFeePayment.objects.filter(installment=current_due_inst).values_list('student_id', flat=True)
        paid_count = len(paid_student_ids)
        unpaid_count = eligible_qs.exclude(id__in=paid_student_ids).count()

        total_collected_amount = StudentFeePayment.objects.filter(installment=current_due_inst).aggregate(
            tot=Sum('amount_paid')
        )['tot'] or Decimal('0.00')
        total_pending_amount = unpaid_count * current_due_inst.amount

    # Recent 5 payments
    recent_payments = StudentFeePayment.objects.select_related('student', 'installment').order_by('-created_at')[:6]

    context = {
        'total_students': total_students,
        'total_staff': total_staff,
        'total_classes': total_classes,
        'today_total': today_total,
        'today_present': today_present,
        'today_absent': today_absent,
        'today_rate': today_rate,
        'class_stats': class_stats,
        'current_due_inst': current_due_inst,
        'paid_count': paid_count,
        'unpaid_count': unpaid_count,
        'total_collected_amount': total_collected_amount,
        'total_pending_amount': total_pending_amount,
        'recent_payments': recent_payments,
        'today': today,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@login_required
def staff_dashboard(request):
    today = date.today()
    total_students = Student.objects.filter(is_active=True).count()
    total_payments = StudentFeePayment.objects.count()
    recent_admissions = Student.objects.order_by('-created_at')[:6]
    recent_payments = StudentFeePayment.objects.select_related('student', 'installment').order_by('-created_at')[:6]

    current_due_inst = FeeInstallment.objects.filter(is_current_due=True).first()
    unpaid_count = 0
    if current_due_inst:
        paid_student_ids = StudentFeePayment.objects.filter(installment=current_due_inst).values_list('student_id', flat=True)
        eligible_qs = Student.objects.filter(is_active=True)
        if current_due_inst.fee_structure.school_class:
            eligible_qs = eligible_qs.filter(current_class=current_due_inst.fee_structure.school_class)
        unpaid_count = eligible_qs.exclude(id__in=paid_student_ids).count()

    context = {
        'total_students': total_students,
        'total_payments': total_payments,
        'recent_admissions': recent_admissions,
        'recent_payments': recent_payments,
        'current_due_inst': current_due_inst,
        'unpaid_count': unpaid_count,
        'today': today
    }
    return render(request, 'dashboard/staff_dashboard.html', context)


@login_required
def teacher_dashboard(request):
    today = date.today()
    user = request.user
    staff_profile = getattr(user, 'staff_profile', None)

    # Class managed by this teacher or fallback
    managed_class = None
    if staff_profile:
        managed_class = staff_profile.managed_classes.first()
    if not managed_class:
        managed_class = SchoolClass.objects.first()

    today_session = None
    students = []
    if managed_class:
        today_session = DailyAttendanceSession.objects.filter(school_class=managed_class, date=today).first()
        students = managed_class.students.filter(is_active=True)

    exams = Exam.objects.filter(is_published=True).order_by('-start_date')[:3]

    context = {
        'staff_profile': staff_profile,
        'managed_class': managed_class,
        'today_session': today_session,
        'students': students,
        'exams': exams,
        'today': today
    }
    return render(request, 'dashboard/teacher_dashboard.html', context)


@login_required
def class_dashboard(request, class_id):
    """
    Class Dashboard: fee, exam, attendance
    """
    school_class = get_object_or_404(SchoolClass.objects.select_related('grade', 'course', 'class_teacher'), pk=class_id)
    students = school_class.students.filter(is_active=True).order_by('roll_number', 'full_name')
    total_students = students.count()

    today = date.today()
    today_session = DailyAttendanceSession.objects.filter(school_class=school_class, date=today).first()

    # 1. Attendance Metrics
    past_sessions = DailyAttendanceSession.objects.filter(school_class=school_class).order_by('-date')[:30]
    total_class_sessions = past_sessions.count()
    if total_class_sessions > 0:
        total_p = sum(s.present_count for s in past_sessions)
        total_slots = sum(s.total_students for s in past_sessions)
        avg_att_rate = round((total_p / total_slots * 100), 1) if total_slots else 0.0
    else:
        avg_att_rate = 0.0

    # 2. Fee Metrics for this class
    current_due_inst = FeeInstallment.objects.filter(
        Q(fee_structure__school_class=school_class) | Q(fee_structure__grade=school_class.grade),
        is_current_due=True
    ).first()
    if not current_due_inst:
        current_due_inst = FeeInstallment.objects.filter(
            Q(fee_structure__school_class=school_class) | Q(fee_structure__grade=school_class.grade)
        ).first()

    paid_students = []
    unpaid_students = []
    fee_collected = Decimal('0.00')
    fee_pending = Decimal('0.00')

    if current_due_inst:
        paid_student_ids = StudentFeePayment.objects.filter(installment=current_due_inst).values_list('student_id', flat=True)
        paid_students = students.filter(id__in=paid_student_ids)
        unpaid_students = students.exclude(id__in=paid_student_ids)
        fee_collected = StudentFeePayment.objects.filter(installment=current_due_inst, student__in=students).aggregate(tot=Sum('amount_paid'))['tot'] or Decimal('0.00')
        fee_pending = unpaid_students.count() * current_due_inst.amount

    # 3. Exam Performance for this class
    latest_exam = Exam.objects.filter(schedules__school_class=school_class).distinct().order_by('-start_date').first()
    exam_stats = []
    if latest_exam:
        schedules = ExamSchedule.objects.filter(exam=latest_exam, school_class=school_class).select_related('subject')
        for sched in schedules:
            marks = sched.student_marks.filter(is_absent=False, marks_obtained__isnull=False)
            cnt = marks.count()
            avg_m = marks.aggregate(avg=Avg('marks_obtained'))['avg'] or 0.0
            exam_stats.append({
                'subject': sched.subject.name,
                'max_marks': sched.max_marks,
                'avg_marks': round(float(avg_m), 1),
                'count': cnt
            })

    all_classes = SchoolClass.objects.all()

    context = {
        'school_class': school_class,
        'all_classes': all_classes,
        'students': students,
        'total_students': total_students,
        'today_session': today_session,
        'avg_att_rate': avg_att_rate,
        'current_due_inst': current_due_inst,
        'paid_students': paid_students,
        'unpaid_students': unpaid_students,
        'fee_collected': fee_collected,
        'fee_pending': fee_pending,
        'latest_exam': latest_exam,
        'exam_stats': exam_stats,
        'today': today
    }
    return render(request, 'dashboard/class_dashboard.html', context)


@login_required
def student_dashboard(request, student_id=None):
    """
    Student / Parent Dashboard:
    - Today's attendance status (Attended or Not)
    - Monthly attendance & percentage
    - Academic year attendance & percentage
    - Marks added for each examination
    - Progress report card view and PDF download
    """
    user = request.user
    if student_id:
        student = get_object_or_404(Student, pk=student_id)
    else:
        # If logged in as parent/student
        student = getattr(user, 'student_profile', None)
        if not student:
            # Fallback for admin or testing
            student = Student.objects.first()

    if not student:
        messages.error(request, "No student profile found.")
        return redirect('home')

    today = date.today()
    today_status = student.get_today_attendance()
    is_attended_today = today_status in ['PRESENT', 'LATE']

    # Monthly attendance stats
    monthly_stats = student.get_monthly_attendance_stats()

    # Yearly attendance stats
    yearly_stats = student.get_yearly_attendance_stats()

    # Examination Marks for each examination
    exams = Exam.objects.filter(academic_year=student.academic_year, is_published=True).order_by('-start_date')
    exam_records = []
    for ex in exams:
        marks = StudentMark.objects.filter(
            student=student,
            exam_schedule__exam=ex
        ).select_related('exam_schedule__subject')

        total_obtained = sum(float(m.marks_obtained or 0) for m in marks if not m.is_absent)
        total_max = sum(float(m.exam_schedule.max_marks) for m in marks)
        pct = round((total_obtained / total_max * 100), 1) if total_max else 0.0

        exam_records.append({
            'exam': ex,
            'marks': marks,
            'total_obtained': total_obtained,
            'total_max': total_max,
            'percentage': pct,
            'has_marks': marks.exists()
        })

    # Fee payments history
    fee_payments = student.fee_payments.select_related('installment__fee_structure').order_by('-payment_date')

    # Pending fees for this student
    all_installments = FeeInstallment.objects.filter(
        Q(fee_structure__school_class=student.current_class) | Q(fee_structure__grade=student.current_class.grade)
    )
    paid_inst_ids = fee_payments.values_list('installment_id', flat=True)
    pending_installments = all_installments.exclude(id__in=paid_inst_ids)
    if not student.vehicle_opted:
        pending_installments = pending_installments.filter(requires_vehicle=False)

    context = {
        'student': student,
        'today': today,
        'today_status': today_status,
        'is_attended_today': is_attended_today,
        'monthly_stats': monthly_stats,
        'yearly_stats': yearly_stats,
        'exam_records': exam_records,
        'fee_payments': fee_payments,
        'pending_installments': pending_installments,
    }
    return render(request, 'dashboard/student_dashboard.html', context)
