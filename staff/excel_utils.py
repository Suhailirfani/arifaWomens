import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from datetime import datetime, date
from accounts.models import User
from staff.models import StaffProfile

def generate_staff_excel_template():
    """
    Generates a pre-formatted Excel workbook (.xlsx) for bulk staff registration.
    Includes instructions, portal role selection, and sample rows.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Staff Upload Template"

    headers = [
        "Staff ID*", "Full Name*", "Designation*", "Department",
        "Gender", "Qualifications", "Phone Number*", "Email Address",
        "Address", "Joining Date (YYYY-MM-DD)",
        "Portal Role (Teacher / Office Staff / Admin)",
        "Portal Username", "Portal Password"
    ]

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
            "ARF-STF-01", "Usthadh Abdul Rahman", "Senior Lecturer in Islamic Studies", "Islamic Studies",
            "Male", "M.A. Arabic, Afzal-ul-Ulama", "9847112233", "abdulrahman@darulmaarif.edu.in",
            "Kodampuzha, Calicut", "2023-06-01", "Teacher",
            "ARF-STF-01", "staff123"
        ],
        [
            "ARF-STF-02", "Prof. Amina Rahmath", "Head of English Department", "Humanities",
            "Female", "M.A. English, B.Ed, SET", "9847223344", "amina.rahmath@darulmaarif.edu.in",
            "Feroke, Calicut", "2023-06-01", "Teacher",
            "amina_prof", "profPass2026"
        ],
        [
            "ARF-STF-03", "Kadeeja Beevi", "Office Superintendent & Accounts", "Administration",
            "Female", "M.Com, Tally Prime Certified", "9847334455", "accounts@darulmaarif.edu.in",
            "Ramanattukara, Calicut", "2024-01-15", "Office Staff",
            "ARF-STF-03", "office123"
        ],
    ]

    for row in samples:
        ws.append(row)

    # Auto-adjust column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 15)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def parse_staff_bulk_excel(file_obj):
    """
    Parses uploaded staff .xlsx file and creates/updates StaffProfile and User accounts.
    Returns: (created_count, updated_count, error_messages)
    """
    if isinstance(file_obj, bytes):
        file_obj = io.BytesIO(file_obj)

    wb = openpyxl.load_workbook(file_obj, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if len(rows) < 2:
        return 0, 0, ["The uploaded spreadsheet is empty or missing data rows."]

    created_count = 0
    updated_count = 0
    errors = []

    # Map headers
    for idx, row in enumerate(rows[1:], start=2):
        if not row or not any(row):
            continue

        staff_id = str(row[0]).strip() if len(row) > 0 and row[0] is not None else ''
        name = str(row[1]).strip() if len(row) > 1 and row[1] is not None else ''

        if not staff_id or not name:
            errors.append(f"Row {idx}: Staff ID and Full Name are mandatory. Row skipped.")
            continue

        designation = str(row[2]).strip() if len(row) > 2 and row[2] is not None else 'Teacher'
        dept = str(row[3]).strip() if len(row) > 3 and row[3] is not None else ''
        gender = str(row[4]).strip() if len(row) > 4 and row[4] is not None else 'Female'
        qualification = str(row[5]).strip() if len(row) > 5 and row[5] is not None else ''
        phone = str(row[6]).strip() if len(row) > 6 and row[6] is not None else ''
        email = str(row[7]).strip() if len(row) > 7 and row[7] is not None else ''
        address = str(row[8]).strip() if len(row) > 8 and row[8] is not None else ''
        
        # Parse joining date
        joining_date = None
        if len(row) > 9 and row[9] is not None:
            raw_date = row[9]
            if isinstance(raw_date, (datetime, date)):
                joining_date = raw_date if isinstance(raw_date, date) else raw_date.date()
            else:
                try:
                    joining_date = datetime.strptime(str(raw_date).strip(), '%Y-%m-%d').date()
                except ValueError:
                    try:
                        joining_date = datetime.strptime(str(raw_date).strip(), '%d/%m/%Y').date()
                    except ValueError:
                        joining_date = None

        # Role determination
        raw_role = str(row[10]).strip().lower() if len(row) > 10 and row[10] is not None else ''
        if 'office' in raw_role or 'account' in raw_role:
            role = User.Role.OFFICE_STAFF
        elif 'admin' in raw_role:
            role = User.Role.ADMIN
        else:
            role = User.Role.TEACHER

        # Username and password
        user_col = str(row[11]).strip() if len(row) > 11 and row[11] is not None else ''
        pass_col = str(row[12]).strip() if len(row) > 12 and row[12] is not None else ''

        username = user_col if user_col else staff_id
        raw_password = pass_col if pass_col else 'staff123'

        user = User.objects.filter(username=username).first()
        if not user:
            name_parts = name.split(' ', 1)
            user = User.objects.create_user(
                username=username,
                password=raw_password,
                role=role,
                first_name=name_parts[0],
                last_name=name_parts[1] if len(name_parts) > 1 else '',
                email=email,
                phone_number=phone
            )
        else:
            user.role = role
            if pass_col:
                user.set_password(raw_password)
            user.save()

        # Update or create staff profile
        staff, created = StaffProfile.objects.update_or_create(
            staff_id=staff_id,
            defaults={
                'user': user,
                'full_name': name,
                'gender': gender if gender in ['Female', 'Male', 'Other'] else 'Female',
                'designation': designation,
                'department': dept,
                'qualification': qualification,
                'phone': phone,
                'email': email,
                'address': address,
                'joining_date': joining_date,
                'is_active': True,
            }
        )

        if created:
            created_count += 1
        else:
            updated_count += 1

    return created_count, updated_count, errors
