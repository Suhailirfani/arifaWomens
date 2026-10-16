from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from datetime import date, datetime, timedelta

from .models import DailyAttendanceSession, StudentAttendanceRecord
from academics.models import SchoolClass
from students.models import Student
from staff.models import StaffProfile

@login_required
def take_attendance(request):
    """
    Daily, class-wise attendance marking page.
    """
    classes = SchoolClass.objects.select_related('grade', 'course').all()
    selected_class_id = request.GET.get('class_id') or request.POST.get('class_id')
    date_str = request.GET.get('date') or request.POST.get('date')

    target_date = date.today()
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = date.today()

    selected_class = None
    if selected_class_id:
        selected_class = SchoolClass.objects.filter(id=selected_class_id).first()
    if not selected_class and classes.exists():
        selected_class = classes.first()

    students = []
    session = None
    records_map = {}

    if selected_class:
        students = selected_class.students.filter(is_active=True).order_by('roll_number', 'full_name')
        session = DailyAttendanceSession.objects.filter(school_class=selected_class, date=target_date).first()
        if session:
            records_map = {r.student_id: r.status for r in session.records.all()}

    if request.method == 'POST' and selected_class:
        remarks = request.POST.get('remarks', '')
        staff_profile = getattr(request.user, 'staff_profile', None)

        session, _ = DailyAttendanceSession.objects.update_or_create(
            school_class=selected_class,
            date=target_date,
            defaults={
                'taken_by': staff_profile,
                'remarks': remarks
            }
        )

        saved_count = 0
        for student in students:
            status_val = request.POST.get(f'status_{student.id}', 'PRESENT')
            StudentAttendanceRecord.objects.update_or_create(
                session=session,
                student=student,
                defaults={'status': status_val}
            )
            saved_count += 1

        messages.success(request, f"Attendance saved successfully for {selected_class.display_name} on {target_date.strftime('%d-%b-%Y')} ({saved_count} students recorded).")
        return redirect(f"/attendance/take/?class_id={selected_class.id}&date={target_date.strftime('%Y-%m-%d')}")

    # Build student roster with current status
    student_rows = []
    p_cnt, a_cnt, l_cnt = 0, 0, 0
    for s in students:
        current_status = records_map.get(s.id, 'PRESENT')
        if current_status == 'PRESENT': p_cnt += 1
        elif current_status == 'ABSENT': a_cnt += 1
        elif current_status == 'LATE': l_cnt += 1

        student_rows.append({
            'student': s,
            'status': current_status
        })

    context = {
        'classes': classes,
        'selected_class': selected_class,
        'target_date': target_date,
        'date_str': target_date.strftime('%Y-%m-%d'),
        'student_rows': student_rows,
        'session': session,
        'p_cnt': p_cnt,
        'a_cnt': a_cnt,
        'l_cnt': l_cnt,
        'total_students': len(students),
    }
    return render(request, 'attendance/take_attendance.html', context)


@login_required
def attendance_history(request):
    classes = SchoolClass.objects.all()
    class_id = request.GET.get('class_id')
    sessions = DailyAttendanceSession.objects.select_related('school_class__grade', 'school_class__course', 'taken_by').order_by('-date')

    if class_id:
        sessions = sessions.filter(school_class_id=class_id)

    context = {
        'sessions': sessions[:50],
        'classes': classes,
        'selected_class_id': class_id
    }
    return render(request, 'attendance/attendance_history.html', context)


@login_required
def api_student_heatmap(request, student_id):
    student = get_object_or_404(Student, pk=student_id)
    today = date.today()
    start_date = today - timedelta(days=90)
    records = StudentAttendanceRecord.objects.filter(
        student=student,
        session__date__gte=start_date
    ).values('session__date', 'status')

    data = [{'date': r['session__date'].strftime('%Y-%m-%d'), 'status': r['status']} for r in records]
    return JsonResponse({'student': student.full_name, 'records': data})
