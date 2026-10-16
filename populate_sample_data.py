import os
import django
from datetime import date, timedelta
from decimal import Decimal
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'arifa_project.settings')
django.setup()

from accounts.models import User
from academics.models import AcademicYear, GradeLevel, Course, SchoolClass, Subject
from staff.models import StaffProfile
from students.models import Student
from attendance.models import DailyAttendanceSession, StudentAttendanceRecord
from fees.models import FeeCategory, FeeStructure, FeeInstallment, StudentFeePayment
from examinations.models import Exam, ExamSchedule, StudentMark

def run():
    print("--- Seeding Database for Arifa Women's Academy, Kodampuzha ---")

    # 1. Academic Year
    ay, _ = AcademicYear.objects.get_or_create(
        name="2026-2027",
        defaults={
            'start_date': date(2026, 6, 1),
            'end_date': date(2027, 3, 31),
            'is_current': True
        }
    )

    # 2. Grade Levels
    grades_data = [
        ("Class 8", GradeLevel.LevelCategory.HIGH_SCHOOL, 1),
        ("Class 9", GradeLevel.LevelCategory.HIGH_SCHOOL, 2),
        ("Class 10", GradeLevel.LevelCategory.HIGH_SCHOOL, 3),
        ("Plus One", GradeLevel.LevelCategory.HIGHER_SECONDARY, 4),
        ("Plus Two", GradeLevel.LevelCategory.HIGHER_SECONDARY, 5),
    ]
    grade_objs = {}
    for name, cat, seq in grades_data:
        g, _ = GradeLevel.objects.get_or_create(name=name, defaults={'level_category': cat, 'sequence': seq})
        grade_objs[name] = g

    # 3. Courses
    courses_data = [
        ("General", "GEN", "General syllabus for high school classes"),
        ("Humanities", "HUM", "Higher Secondary Humanities with Sociology, Political Science, History, Economics"),
        ("Commerce", "COM", "Higher Secondary Commerce with Accountancy, Business Studies, Economics, Computer Applications"),
        ("Science", "SCI", "Higher Secondary Science with Physics, Chemistry, Biology/Maths"),
    ]
    course_objs = {}
    for name, code, desc in courses_data:
        c, _ = Course.objects.get_or_create(name=name, defaults={'code': code, 'description': desc})
        course_objs[name] = c

    # 4. Users & Staff Profiles
    # Admin User
    admin_user, created = User.objects.get_or_create(username='admin', defaults={
        'email': 'principal@arifa.edu.in',
        'first_name': 'Dr. Fathima',
        'last_name': 'Rahman',
        'role': User.Role.ADMIN,
        'is_staff': True,
        'is_superuser': True,
        'phone_number': '+91 98470 12345'
    })
    if created:
        admin_user.set_password('admin123')
        admin_user.save()

    StaffProfile.objects.get_or_create(
        staff_id='ARF-ADM-01',
        defaults={
            'user': admin_user,
            'full_name': 'Dr. Fathima Rahman',
            'gender': 'Female',
            'designation': 'Principal & Administrator',
            'department': 'Administration',
            'qualification': 'Ph.D in Education, M.A. English, B.Ed',
            'phone': '+91 98470 12345',
            'email': 'principal@arifa.edu.in',
            'address': 'Kodampuzha, Calicut, Kerala',
            'joining_date': date(2020, 5, 15)
        }
    )

    # Office Staff User
    office_user, created = User.objects.get_or_create(username='staff', defaults={
        'email': 'office@arifa.edu.in',
        'first_name': 'Amina',
        'last_name': 'Beevi',
        'role': User.Role.OFFICE_STAFF,
        'is_staff': True,
        'phone_number': '+91 94471 23456'
    })
    if created:
        office_user.set_password('staff123')
        office_user.save()

    StaffProfile.objects.get_or_create(
        staff_id='ARF-OFF-01',
        defaults={
            'user': office_user,
            'full_name': 'Amina Beevi',
            'gender': 'Female',
            'designation': 'Office Superintendent',
            'department': 'Administration',
            'qualification': 'M.Com, PGDCA',
            'phone': '+91 94471 23456',
            'email': 'office@arifa.edu.in',
            'address': 'Feroke, Kozhikode, Kerala',
            'joining_date': date(2021, 6, 1)
        }
    )

    # Teacher User (Class Teacher of Plus One Humanities)
    teacher_user, created = User.objects.get_or_create(username='teacher', defaults={
        'email': 'sameera@arifa.edu.in',
        'first_name': 'Sameera',
        'last_name': 'K.P.',
        'role': User.Role.TEACHER,
        'phone_number': '+91 97452 34567'
    })
    if created:
        teacher_user.set_password('teacher123')
        teacher_user.save()

    teacher_profile, _ = StaffProfile.objects.get_or_create(
        staff_id='ARF-TCH-01',
        defaults={
            'user': teacher_user,
            'full_name': 'Prof. Sameera K.P.',
            'gender': 'Female',
            'designation': 'Senior Lecturer in Sociology',
            'department': 'Humanities',
            'qualification': 'M.A. Sociology, B.Ed, SET',
            'phone': '+91 97452 34567',
            'email': 'sameera@arifa.edu.in',
            'address': 'Ramanattukara, Kozhikode',
            'joining_date': date(2022, 6, 10)
        }
    )

    # Second Teacher
    teacher2_user, created = User.objects.get_or_create(username='khadija', defaults={
        'email': 'khadija@arifa.edu.in',
        'first_name': 'Khadija',
        'last_name': 'M.',
        'role': User.Role.TEACHER,
        'phone_number': '+91 96453 45678'
    })
    if created:
        teacher2_user.set_password('teacher123')
        teacher2_user.save()

    teacher2_profile, _ = StaffProfile.objects.get_or_create(
        staff_id='ARF-TCH-02',
        defaults={
            'user': teacher2_user,
            'full_name': 'Khadija M.',
            'gender': 'Female',
            'designation': 'Commerce Faculty',
            'department': 'Commerce',
            'qualification': 'M.Com, B.Ed, NET',
            'phone': '+91 96453 45678',
            'email': 'khadija@arifa.edu.in',
            'address': 'Pantheerankavu, Kozhikode',
            'joining_date': date(2023, 6, 1)
        }
    )

    # 5. School Classes (Combined Grade and Course!)
    # Plus One Humanities
    c_p1_hum, _ = SchoolClass.objects.get_or_create(
        grade=grade_objs["Plus One"],
        course=course_objs["Humanities"],
        section="A",
        academic_year=ay,
        defaults={'room_number': 'Room 101', 'class_teacher': teacher_profile}
    )
    # Plus One Commerce
    c_p1_com, _ = SchoolClass.objects.get_or_create(
        grade=grade_objs["Plus One"],
        course=course_objs["Commerce"],
        section="A",
        academic_year=ay,
        defaults={'room_number': 'Room 102', 'class_teacher': teacher2_profile}
    )
    # Plus Two Humanities
    c_p2_hum, _ = SchoolClass.objects.get_or_create(
        grade=grade_objs["Plus Two"],
        course=course_objs["Humanities"],
        section="A",
        academic_year=ay,
        defaults={'room_number': 'Room 201'}
    )
    # Plus Two Commerce
    c_p2_com, _ = SchoolClass.objects.get_or_create(
        grade=grade_objs["Plus Two"],
        course=course_objs["Commerce"],
        section="A",
        academic_year=ay,
        defaults={'room_number': 'Room 202'}
    )
    # Class 10 General
    c_10, _ = SchoolClass.objects.get_or_create(
        grade=grade_objs["Class 10"],
        course=course_objs["General"],
        section="A",
        academic_year=ay,
        defaults={'room_number': 'Room 003'}
    )
    # Class 9 General
    c_9, _ = SchoolClass.objects.get_or_create(
        grade=grade_objs["Class 9"],
        course=course_objs["General"],
        section="A",
        academic_year=ay,
        defaults={'room_number': 'Room 002'}
    )
    # Class 8 General
    c_8, _ = SchoolClass.objects.get_or_create(
        grade=grade_objs["Class 8"],
        course=course_objs["General"],
        section="A",
        academic_year=ay,
        defaults={'room_number': 'Room 001'}
    )

    # 6. Subjects
    subjects_info = [
        ("English Core", "ENG-01", [c_p1_hum, c_p1_com, c_p2_hum, c_p2_com, c_10]),
        ("Sociology", "SOC-01", [c_p1_hum, c_p2_hum]),
        ("Political Science", "POL-01", [c_p1_hum, c_p2_hum]),
        ("Economics", "ECO-01", [c_p1_hum, c_p1_com, c_p2_hum, c_p2_com]),
        ("History", "HIS-01", [c_p1_hum, c_p2_hum]),
        ("Accountancy", "ACC-01", [c_p1_com, c_p2_com]),
        ("Business Studies", "BST-01", [c_p1_com, c_p2_com]),
        ("Arabic", "ARB-01", [c_p1_hum, c_p1_com, c_p2_hum, c_p2_com, c_10]),
        ("Islamic Studies", "ISL-01", [c_p1_hum, c_p1_com, c_p2_hum, c_p2_com, c_10]),
        ("Mathematics", "MAT-01", [c_10, c_9, c_8]),
        ("General Science", "SCI-01", [c_10, c_9, c_8]),
    ]
    created_subjects = {}
    for s_name, s_code, class_list in subjects_info:
        subj, _ = Subject.objects.get_or_create(name=s_name, defaults={'code': s_code})
        subj.school_classes.set(class_list)
        created_subjects[s_name] = subj

    # 7. Students
    # Student User for Parent / Student Portal
    student_user, created = User.objects.get_or_create(username='student', defaults={
        'email': 'aisha.nihala@student.arifa.edu.in',
        'first_name': 'Aisha',
        'last_name': 'Nihala',
        'role': User.Role.PARENT,
        'phone_number': '+91 99460 11223'
    })
    if created:
        student_user.set_password('student123')
        student_user.save()

    students_data_p1_hum = [
        ("ARF-2026-001", "01", "Aisha Nihala", "Abdul Rahman K.", "+91 99460 11223", True, "Kodampuzha Route A", student_user),
        ("ARF-2026-002", "02", "Fathima Sana", "Muhammed Musthafa", "+91 98471 22334", True, "Feroke Route B", None),
        ("ARF-2026-003", "03", "Hiba Mariyam", "Usman Kutty", "+91 97452 33445", False, "", None),
        ("ARF-2026-004", "04", "Raniya Sherin", "Shareef V.P.", "+91 96453 44556", True, "Ramanattukara Route", None),
        ("ARF-2026-005", "05", "Shahana Nasrin", "Noufal K.", "+91 95454 55667", False, "", None),
        ("ARF-2026-006", "06", "Lubna Farheen", "Ibrahim Khalil", "+91 94465 66778", True, "Kodampuzha Route B", None),
        ("ARF-2026-007", "07", "Rida Fatima", "Basheer Ahmed", "+91 93476 77889", False, "", None),
        ("ARF-2026-008", "08", "Thasneem Banu", "Shamsudheen P.", "+91 92487 88990", True, "Pantheerankavu Route", None),
        ("ARF-2026-009", "09", "Safna Yasmin", "Hamza Ali", "+91 91498 99001", True, "Feroke Route A", None),
        ("ARF-2026-010", "10", "Anshidha Mariam", "Aboobacker Siddique", "+91 90509 00112", False, "", None),
    ]

    p1_hum_students = []
    for adm, roll, name, guardian, phone, v_opt, route, usr in students_data_p1_hum:
        st, _ = Student.objects.get_or_create(
            admission_number=adm,
            defaults={
                'roll_number': roll,
                'full_name': name,
                'user': usr,
                'gender': 'Female',
                'current_class': c_p1_hum,
                'academic_year': ay,
                'father_or_guardian_name': guardian,
                'guardian_phone': phone,
                'guardian_email': f"{name.lower().replace(' ', '.')}@gmail.com",
                'address': f"{guardian}'s Residence, Near Kodampuzha, Calicut",
                'date_of_birth': date(2009, 4, 12),
                'admission_date': date(2026, 6, 2),
                'vehicle_opted': v_opt,
                'vehicle_route': route,
                'blood_group': 'B+'
            }
        )
        p1_hum_students.append(st)

    # Plus One Commerce Students
    students_data_p1_com = [
        ("ARF-2026-021", "01", "Naseera K.", "Kamaludheen K.", "+91 99461 33441", True, "Feroke Route A"),
        ("ARF-2026-022", "02", "Anshida Parveen", "Moideenkutty T.", "+91 98472 44552", False, ""),
        ("ARF-2026-023", "03", "Minha Fathima", "Zakkariya C.", "+91 97453 55663", True, "Kodampuzha Route A"),
        ("ARF-2026-024", "04", "Shamna Sherin", "Asharaf Ali", "+91 96454 66774", False, ""),
        ("ARF-2026-025", "05", "Jumana Thasnim", "Siddique Hassan", "+91 95455 77885", True, "Ramanattukara Route"),
    ]
    p1_com_students = []
    for adm, roll, name, guardian, phone, v_opt, route in students_data_p1_com:
        st, _ = Student.objects.get_or_create(
            admission_number=adm,
            defaults={
                'roll_number': roll,
                'full_name': name,
                'gender': 'Female',
                'current_class': c_p1_com,
                'academic_year': ay,
                'father_or_guardian_name': guardian,
                'guardian_phone': phone,
                'guardian_email': f"{name.lower().replace(' ', '.')}@gmail.com",
                'address': f"Kozhikode, Kerala",
                'date_of_birth': date(2009, 8, 20),
                'admission_date': date(2026, 6, 2),
                'vehicle_opted': v_opt,
                'vehicle_route': route,
                'blood_group': 'O+'
            }
        )
        p1_com_students.append(st)

    # Class 10 Students
    students_data_c10 = [
        ("ARF-2026-051", "01", "Ayisha Rifa", "Mansoor Ali", "+91 99465 11111", True, "Kodampuzha Route A"),
        ("ARF-2026-052", "02", "Fathimathu Zahra", "Rashid K.T.", "+91 98476 22222", False, ""),
        ("ARF-2026-053", "03", "Nuha Mariyam", "Shihabudheen", "+91 97457 33333", True, "Feroke Route B"),
    ]
    for adm, roll, name, guardian, phone, v_opt, route in students_data_c10:
        Student.objects.get_or_create(
            admission_number=adm,
            defaults={
                'roll_number': roll,
                'full_name': name,
                'gender': 'Female',
                'current_class': c_10,
                'academic_year': ay,
                'father_or_guardian_name': guardian,
                'guardian_phone': phone,
                'address': "Calicut, Kerala",
                'date_of_birth': date(2010, 3, 15),
                'admission_date': date(2026, 6, 2),
                'vehicle_opted': v_opt,
                'vehicle_route': route,
                'blood_group': 'A+'
            }
        )

    # 8. Attendance Records (Last 60 school days)
    print("Generating Attendance records...")
    today = date.today()
    start_history = today - timedelta(days=65)
    
    cur_date = start_history
    school_days = []
    while cur_date <= today:
        # Exclude Sunday (weekday == 6)
        if cur_date.weekday() != 6:
            school_days.append(cur_date)
        cur_date += timedelta(days=1)

    for day in school_days:
        session, _ = DailyAttendanceSession.objects.get_or_create(
            school_class=c_p1_hum,
            date=day,
            defaults={'taken_by': teacher_profile, 'remarks': 'Regular Class Attendance'}
        )
        for st in p1_hum_students:
            # High attendance rate for Aisha Nihala, occasional absent for others
            if st.admission_number == "ARF-2026-001":
                status = 'PRESENT'
                if day.weekday() == 4 and day.day % 14 == 0:
                    status = 'ABSENT'
            else:
                r = random.random()
                if r < 0.88:
                    status = 'PRESENT'
                elif r < 0.95:
                    status = 'ABSENT'
                else:
                    status = 'LATE'
            
            # Ensure today is marked PRESENT for Aisha Nihala
            if day == today and st.admission_number == "ARF-2026-001":
                status = 'PRESENT'

            StudentAttendanceRecord.objects.get_or_create(
                session=session,
                student=st,
                defaults={'status': status}
            )

    # 9. Fees Structure & Installments
    # Fee Categories
    cat_installment, _ = FeeCategory.objects.get_or_create(
        name="Course Fee (Installments)",
        defaults={'fee_type': FeeCategory.FeeType.INSTALLMENT, 'description': 'Academic year tuition and course fee paid in 3 installments'}
    )
    cat_vehicle, _ = FeeCategory.objects.get_or_create(
        name="Vehicle / Transportation Fee",
        defaults={'fee_type': FeeCategory.FeeType.MONTHLY, 'description': 'Monthly recurring bus fee'}
    )

    # Course Fee Structure for Plus One Humanities
    struct_p1_hum, _ = FeeStructure.objects.get_or_create(
        title="Plus One Humanities - Annual Course Fee",
        academic_year=ay,
        category=cat_installment,
        defaults={'school_class': c_p1_hum, 'total_amount': Decimal('30000.00'), 'description': 'Full year course fee payable in 3 installments'}
    )

    inst1, _ = FeeInstallment.objects.get_or_create(
        fee_structure=struct_p1_hum,
        installment_number=1,
        defaults={
            'title': '1st Installment (Term 1 / Admission)',
            'amount': Decimal('12000.00'),
            'due_date': date(2026, 7, 15),
            'is_current_due': True,
        }
    )
    inst2, _ = FeeInstallment.objects.get_or_create(
        fee_structure=struct_p1_hum,
        installment_number=2,
        defaults={
            'title': '2nd Installment (Term 2)',
            'amount': Decimal('10000.00'),
            'due_date': date(2026, 11, 15),
            'is_current_due': False,
        }
    )
    inst3, _ = FeeInstallment.objects.get_or_create(
        fee_structure=struct_p1_hum,
        installment_number=3,
        defaults={
            'title': '3rd Installment (Final Term)',
            'amount': Decimal('8000.00'),
            'due_date': date(2027, 2, 15),
            'is_current_due': False,
        }
    )

    # Monthly Vehicle Fee Structure
    struct_vehicle, _ = FeeStructure.objects.get_or_create(
        title="Academy Vehicle Fee 2026-27",
        academic_year=ay,
        category=cat_vehicle,
        defaults={'total_amount': Decimal('15000.00'), 'description': 'Monthly transportation fee for bus route subscribers'}
    )
    
    inst_bus_oct, _ = FeeInstallment.objects.get_or_create(
        fee_structure=struct_vehicle,
        installment_number=10,
        defaults={
            'title': 'October 2026 Vehicle Fee',
            'amount': Decimal('1500.00'),
            'due_date': date(2026, 10, 10),
            'is_current_due': True,
            'requires_vehicle': True,
            'month': 10,
            'year': 2026
        }
    )

    # Payments: Let Aisha Nihala and some students pay Installment 1, leave others as unpaid (defaulters)
    paid_students = p1_hum_students[:6]
    unpaid_students = p1_hum_students[6:]

    for idx, st in enumerate(paid_students, 1):
        rec_no = f"REC-2026-00{idx}"
        StudentFeePayment.objects.get_or_create(
            receipt_number=rec_no,
            defaults={
                'student': st,
                'installment': inst1,
                'amount_paid': Decimal('12000.00'),
                'payment_date': date(2026, 7, 10),
                'payment_mode': StudentFeePayment.PaymentMode.UPI,
                'transaction_id': f"UPI2026071000{idx}",
                'remarks': 'Term 1 Course Fee Paid Online',
                'collected_by': office_user
            }
        )

    # Vehicle fee payment for Aisha Nihala and Fathima Sana
    StudentFeePayment.objects.get_or_create(
        receipt_number="REC-2026-V01",
        defaults={
            'student': p1_hum_students[0], # Aisha Nihala
            'installment': inst_bus_oct,
            'amount_paid': Decimal('1500.00'),
            'payment_date': date(2026, 10, 5),
            'payment_mode': StudentFeePayment.PaymentMode.UPI,
            'transaction_id': 'UPI2026100501',
            'remarks': 'October Bus Fee Paid',
            'collected_by': office_user
        }
    )

    # 10. Examinations & Marks
    exam_term1, _ = Exam.objects.get_or_create(
        name="First Terminal Examination 2026",
        academic_year=ay,
        defaults={
            'start_date': date(2026, 9, 15),
            'end_date': date(2026, 9, 25),
            'is_published': True
        }
    )

    exam_midterm, _ = Exam.objects.get_or_create(
        name="Mid-Term Examination 2026",
        academic_year=ay,
        defaults={
            'start_date': date(2026, 11, 20),
            'end_date': date(2026, 11, 30),
            'is_published': True
        }
    )

    # Exam Schedules for Plus One Humanities
    subjects_p1_hum = [
        created_subjects["English Core"],
        created_subjects["Sociology"],
        created_subjects["Political Science"],
        created_subjects["Economics"],
        created_subjects["History"],
        created_subjects["Arabic"],
        created_subjects["Islamic Studies"],
    ]

    schedules = []
    for i, subj in enumerate(subjects_p1_hum):
        sched, _ = ExamSchedule.objects.get_or_create(
            exam=exam_term1,
            school_class=c_p1_hum,
            subject=subj,
            defaults={
                'exam_date': date(2026, 9, 15) + timedelta(days=i),
                'max_marks': Decimal('100.00'),
                'pass_marks': Decimal('35.00')
            }
        )
        schedules.append(sched)

    # Enter marks for Aisha Nihala and others
    aisha_marks = [94.0, 96.5, 91.0, 89.5, 93.0, 98.0, 95.0]
    for sched, m in zip(schedules, aisha_marks):
        StudentMark.objects.get_or_create(
            exam_schedule=sched,
            student=p1_hum_students[0],
            defaults={
                'marks_obtained': Decimal(str(m)),
                'is_absent': False,
                'remarks': 'Outstanding performance'
            }
        )

    # Enter marks for rest of class
    for st in p1_hum_students[1:]:
        for sched in schedules:
            m = random.randint(45, 92)
            StudentMark.objects.get_or_create(
                exam_schedule=sched,
                student=st,
                defaults={
                    'marks_obtained': Decimal(str(m)),
                    'is_absent': False
                }
            )

    print("--- Sample Data Successfully Seeded! ---")
    print(f"Users created:\n- admin / admin123 (Administrator)\n- staff / staff123 (Office Staff)\n- teacher / teacher123 (Teacher)\n- student / student123 (Student / Parent)")

if __name__ == '__main__':
    run()
