import io
from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from decimal import Decimal

from accounts.models import User
from academics.models import AcademicYear, GradeLevel, Course, SchoolClass, Subject
from staff.models import StaffProfile
from students.models import Student
from attendance.models import DailyAttendanceSession, StudentAttendanceRecord
from fees.models import FeeCategory, FeeStructure, FeeInstallment, StudentFeePayment
from examinations.models import Exam, ExamSchedule, StudentMark

class SystemFlowTest(TestCase):
    def setUp(self):
        # 1. Academic Year
        self.ay = AcademicYear.objects.create(
            name="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 3, 31),
            is_current=True
        )

        # 2. Grade & Course
        self.grade_hss = GradeLevel.objects.create(name="Plus One", level_category=GradeLevel.LevelCategory.HIGHER_SECONDARY, sequence=4)
        self.course_hum = Course.objects.create(name="Humanities", code="HUM")

        # 3. Class (Combined grade & course)
        self.school_class = SchoolClass.objects.create(
            grade=self.grade_hss,
            course=self.course_hum,
            section="A",
            academic_year=self.ay,
            room_number="Room 101"
        )

        # 4. Users
        self.admin_user = User.objects.create_user(username='admin_test', password='password123', role=User.Role.ADMIN, is_staff=True)
        self.staff_user = User.objects.create_user(username='staff_test', password='password123', role=User.Role.OFFICE_STAFF)
        self.teacher_user = User.objects.create_user(username='teacher_test', password='password123', role=User.Role.TEACHER)
        self.student_user = User.objects.create_user(username='student_test', password='password123', role=User.Role.PARENT)

        # 5. Staff Profile
        self.staff_profile = StaffProfile.objects.create(
            user=self.teacher_user,
            staff_id="STF-01",
            full_name="Sameera K.P.",
            phone="9847000000"
        )
        self.school_class.class_teacher = self.staff_profile
        self.school_class.save()

        # 6. Student
        self.student = Student.objects.create(
            user=self.student_user,
            admission_number="ARF-TEST-01",
            roll_number="01",
            full_name="Aisha Nihala",
            current_class=self.school_class,
            academic_year=self.ay,
            father_or_guardian_name="Abdul Rahman",
            guardian_phone="9946000000",
            vehicle_opted=True,
            vehicle_route="Kodampuzha Route"
        )

        # 7. Fee Installment
        self.fee_cat = FeeCategory.objects.create(name="Course Fee", fee_type=FeeCategory.FeeType.INSTALLMENT)
        self.fee_struct = FeeStructure.objects.create(
            title="Plus One Humanities Fee",
            category=self.fee_cat,
            school_class=self.school_class,
            academic_year=self.ay,
            total_amount=Decimal('30000.00')
        )
        self.installment = FeeInstallment.objects.create(
            fee_structure=self.fee_struct,
            title="1st Installment",
            installment_number=1,
            amount=Decimal('12000.00'),
            due_date=date(2026, 7, 15),
            is_current_due=True
        )

        # 8. Exam & Schedule
        self.exam = Exam.objects.create(
            name="Terminal Exam 1",
            academic_year=self.ay,
            start_date=date(2026, 9, 15),
            end_date=date(2026, 9, 25)
        )
        self.subject = Subject.objects.create(name="English Core", code="ENG-01")
        self.schedule = ExamSchedule.objects.create(
            exam=self.exam,
            school_class=self.school_class,
            subject=self.subject,
            exam_date=date(2026, 9, 15),
            max_marks=Decimal('100.00'),
            pass_marks=Decimal('35.00')
        )
        self.mark = StudentMark.objects.create(
            exam_schedule=self.schedule,
            student=self.student,
            marks_obtained=Decimal('92.00')
        )

        self.client = Client()

    def test_home_page(self):
        resp = self.client.get(reverse('home'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Arifa Women's Academy")
        self.assertContains(resp, "Humanities")

    def test_admin_dashboard(self):
        self.client.login(username='admin_test', password='password123')
        resp = self.client.get(reverse('dashboard:admin_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Active Fee Due")

    def test_class_dashboard(self):
        self.client.login(username='admin_test', password='password123')
        resp = self.client.get(reverse('dashboard:class_dashboard', kwargs={'class_id': self.school_class.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Attendance Performance")
        self.assertContains(resp, "Class Fee Status")
        self.assertContains(resp, "Exam Performance")

    def test_student_dashboard(self):
        # Create an attendance session for today marked PRESENT
        session = DailyAttendanceSession.objects.create(
            school_class=self.school_class,
            date=date.today(),
            taken_by=self.staff_profile
        )
        StudentAttendanceRecord.objects.create(
            session=session,
            student=self.student,
            status='PRESENT'
        )

        self.client.login(username='student_test', password='password123')
        resp = self.client.get(reverse('dashboard:student_dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Attended Today")
        self.assertContains(resp, "Monthly Attendance")
        self.assertContains(resp, "Academic Year Attendance")

    def test_take_attendance_flow(self):
        self.client.login(username='teacher_test', password='password123')
        today_str = date.today().strftime('%Y-%m-%d')
        post_data = {
            'class_id': self.school_class.id,
            'date': today_str,
            f'status_{self.student.id}': 'PRESENT',
            'remarks': 'Test attendance run'
        }
        resp = self.client.post(reverse('attendance:take_attendance'), post_data)
        self.assertEqual(resp.status_code, 302)
        record = StudentAttendanceRecord.objects.filter(student=self.student, session__date=date.today()).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.status, 'PRESENT')

    def test_fee_defaulters_and_pdf(self):
        self.client.login(username='admin_test', password='password123')
        # Aisha Nihala is currently unpaid
        resp = self.client.get(reverse('fees:fee_defaulters_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Aisha Nihala")

        # Test PDF export
        pdf_resp = self.client.get(reverse('fees:download_defaulters_pdf'))
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp['Content-Type'], 'application/pdf')
        self.assertTrue(len(pdf_resp.content) > 1000)

    def test_progress_report_pdf(self):
        self.client.login(username='admin_test', password='password123')
        resp = self.client.get(reverse('examinations:progress_report', kwargs={'student_id': self.student.id, 'exam_id': self.exam.id}))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "English Core")

        # PDF download
        pdf_resp = self.client.get(reverse('examinations:download_progress_report_pdf', kwargs={'student_id': self.student.id, 'exam_id': self.exam.id}))
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp['Content-Type'], 'application/pdf')
        self.assertTrue(len(pdf_resp.content) > 1000)

    def test_bulk_template_download(self):
        self.client.login(username='admin_test', password='password123')
        resp = self.client.get(reverse('students:download_template'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
