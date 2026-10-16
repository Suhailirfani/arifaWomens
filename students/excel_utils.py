import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime, date
from academics.models import AcademicYear, GradeLevel, Course, SchoolClass
from students.models import Student

def generate_student_excel_template():
    """
    Generates a pre-formatted Excel workbook (.xlsx) for bulk student registration.
    Includes instructions and sample rows.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Student Upload Template"

    headers = [
        "Admission Number*", "Roll No", "Full Name*", "Date of Birth (YYYY-MM-DD)",
        "Gender", "Grade Level*", "Course Name*", "Section*",
        "Father / Guardian Name*", "Guardian Phone*", "Guardian Email",
        "Address", "Vehicle Opted (Yes/No)", "Vehicle Route", "Blood Group"
    ]

    # Header styling
    header_fill = PatternFill(start_color="9F1239", end_color="9F1239", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.append(headers)
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align

    # Sample rows
    samples = [
        [
            "ARF-2026-101", "01", "Mariyam Nabeel", "2009-05-14", "Female",
            "Plus One", "Humanities", "A", "Nabeel K.", "9847111222",
            "mariyam@gmail.com", "Kodampuzha, Calicut", "Yes", "Kodampuzha Route A", "O+"
        ],
        [
            "ARF-2026-102", "02", "Zehra Fathima", "2009-08-22", "Female",
            "Plus One", "Commerce", "A", "Musthafa P.", "9847222333",
            "zehra@gmail.com", "Feroke, Calicut", "No", "", "B+"
        ],
        [
            "ARF-2026-103", "01", "Rida Mariyam", "2010-03-10", "Female",
            "Class 10", "General", "A", "Ibrahimkutty", "9847333444",
            "", "Ramanattukara", "Yes", "Feroke Route B", "A+"
        ]
    ]

    for row in samples:
        ws.append(row)

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def parse_student_bulk_excel(file_obj, current_academic_year=None):
    """
    Parses an uploaded .xlsx file and imports students into the database.
    Returns: (created_count, updated_count, error_list)
    """
    if not current_academic_year:
        current_academic_year = AcademicYear.objects.filter(is_current=True).first()
        if not current_academic_year:
            current_academic_year = AcademicYear.objects.first()

    wb = openpyxl.load_workbook(file_obj, data_only=True)
    ws = wb.active

    created_count = 0
    updated_count = 0
    errors = []

    # Expected column mapping
    # 0: Adm No, 1: Roll, 2: Name, 3: DOB, 4: Gender, 5: Grade, 6: Course, 7: Section
    # 8: Guardian, 9: Phone, 10: Email, 11: Address, 12: Vehicle, 13: Route, 14: Blood
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or not any(row):
            continue

        adm_no = str(row[0]).strip() if row[0] is not None else ''
        name = str(row[2]).strip() if len(row) > 2 and row[2] is not None else ''
        grade_name = str(row[5]).strip() if len(row) > 5 and row[5] is not None else ''
        course_name = str(row[6]).strip() if len(row) > 6 and row[6] is not None else ''
        section = str(row[7]).strip() if len(row) > 7 and row[7] is not None else 'A'
        guardian = str(row[8]).strip() if len(row) > 8 and row[8] is not None else ''
        phone = str(row[9]).strip() if len(row) > 9 and row[9] is not None else ''

        if not adm_no or not name:
            errors.append(f"Row {row_idx}: Skipped. Admission Number and Full Name are mandatory.")
            continue

        # Resolve Grade Level
        grade = GradeLevel.objects.filter(name__iexact=grade_name).first()
        if not grade:
            # Fallback or create
            grade = GradeLevel.objects.filter(name__icontains=grade_name).first()
            if not grade:
                errors.append(f"Row {row_idx}: Invalid Grade Level '{grade_name}'.")
                continue

        # Resolve Course
        course = Course.objects.filter(name__iexact=course_name).first()
        if not course:
            course = Course.objects.filter(name__icontains=course_name).first()
            if not course:
                errors.append(f"Row {row_idx}: Invalid Course '{course_name}'.")
                continue

        # Resolve or create SchoolClass
        school_class, _ = SchoolClass.objects.get_or_create(
            grade=grade,
            course=course,
            section=section,
            academic_year=current_academic_year,
            defaults={'room_number': ''}
        )

        # Parse DOB
        dob_val = row[3] if len(row) > 3 else None
        dob = None
        if isinstance(dob_val, (datetime, date)):
            dob = dob_val if isinstance(dob_val, date) else dob_val.date()
        elif dob_val:
            try:
                dob = datetime.strptime(str(dob_val).strip()[:10], '%Y-%m-%d').date()
            except Exception:
                dob = None

        roll_no = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ''
        gender = str(row[4]).strip() if len(row) > 4 and row[4] is not None else 'Female'
        email = str(row[10]).strip() if len(row) > 10 and row[10] is not None else ''
        address = str(row[11]).strip() if len(row) > 11 and row[11] is not None else ''
        vehicle_str = str(row[12]).strip().lower() if len(row) > 12 and row[12] is not None else 'no'
        vehicle_opted = vehicle_str in ['yes', 'y', 'true', '1']
        route = str(row[13]).strip() if len(row) > 13 and row[13] is not None else ''
        blood_group = str(row[14]).strip() if len(row) > 14 and row[14] is not None else ''

        student, created = Student.objects.update_or_create(
            admission_number=adm_no,
            defaults={
                'roll_number': roll_no,
                'full_name': name,
                'current_class': school_class,
                'academic_year': current_academic_year,
                'date_of_birth': dob,
                'gender': gender,
                'father_or_guardian_name': guardian,
                'guardian_phone': phone,
                'guardian_email': email,
                'address': address,
                'vehicle_opted': vehicle_opted,
                'vehicle_route': route,
                'blood_group': blood_group,
            }
        )

        if created:
            created_count += 1
        else:
            updated_count += 1

    return created_count, updated_count, errors
