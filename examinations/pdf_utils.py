import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime

def generate_progress_report_pdf(student, exam, mark_records):
    """
    Generates a formal, beautiful Progress Report Card PDF for a student and exam.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'SchoolTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#9F1239'),
        alignment=1
    )
    sub_title = ParagraphStyle(
        'SubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        alignment=1
    )
    report_tag = ParagraphStyle(
        'RepTag',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=colors.HexColor('#1E293B'),
        alignment=1
    )
    cell_bold = ParagraphStyle('CBold', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#1E293B'))
    cell_norm = ParagraphStyle('CNorm', fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#334155'))
    table_hdr = ParagraphStyle('THdr', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white, alignment=1)
    table_center = ParagraphStyle('TCenter', fontName='Helvetica', fontSize=9, textColor=colors.HexColor('#1E293B'), alignment=1)

    # Header
    story.append(Paragraph("DARUL MA'ARIF WOMEN'S ACADEMY", title_style))
    story.append(Paragraph("Kodampuzha, Kozhikode, Kerala - 673014 &bull; Affiliated to Board of Secondary Education", sub_title))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"<b>STUDENT PROGRESS REPORT &bull; {exam.name.upper()}</b>", report_tag))
    story.append(Paragraph(f"Academic Session: {exam.academic_year.name}", sub_title))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#E25B78'), spaceAfter=12))

    # Student Details Grid
    meta_info = [
        [Paragraph("<b>Student Name:</b>", cell_bold), Paragraph(student.full_name, cell_bold),
         Paragraph("<b>Admission No:</b>", cell_bold), Paragraph(student.admission_number, cell_norm)],
        [Paragraph("<b>Class & Course:</b>", cell_bold), Paragraph(student.current_class.display_name, cell_norm),
         Paragraph("<b>Roll Number:</b>", cell_bold), Paragraph(student.roll_number or '-', cell_norm)],
        [Paragraph("<b>Guardian's Name:</b>", cell_bold), Paragraph(student.father_or_guardian_name, cell_norm),
         Paragraph("<b>Date of Birth:</b>", cell_bold), Paragraph(student.date_of_birth.strftime('%d-%b-%Y') if student.date_of_birth else '-', cell_norm)],
        [Paragraph("<b>Class Teacher:</b>", cell_bold), Paragraph(student.current_class.class_teacher.full_name if student.current_class.class_teacher else 'Faculty Mentor', cell_norm),
         Paragraph("<b>Issue Date:</b>", cell_bold), Paragraph(datetime.now().strftime('%d-%b-%Y'), cell_norm)],
    ]
    meta_table = Table(meta_info, colWidths=[95, 175, 95, 155])
    meta_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9FC')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # Marks Table
    marks_table_data = [
        [
            Paragraph("#", table_hdr),
            Paragraph("Subject", ParagraphStyle('H1', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
            Paragraph("Max Marks", table_hdr),
            Paragraph("Pass Marks", table_hdr),
            Paragraph("Marks Scored", table_hdr),
            Paragraph("Percentage", table_hdr),
            Paragraph("Grade", table_hdr),
            Paragraph("Remarks", ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=9, textColor=colors.white)),
        ]
    ]

    total_max = 0
    total_obtained = 0

    for idx, rec in enumerate(mark_records, 1):
        sched = rec.exam_schedule
        max_m = float(sched.max_marks)
        total_max += max_m
        
        if rec.is_absent:
            scored_str = "<font color='#DC2626'><b>ABS</b></font>"
            pct_str = "-"
            grade_str = "ABS"
        elif rec.marks_obtained is not None:
            m = float(rec.marks_obtained)
            total_obtained += m
            scored_str = f"<b>{m:.1f}</b>"
            pct = (m / max_m * 100) if max_m else 0
            pct_str = f"{pct:.1f}%"
            grade_str = rec.letter_grade
        else:
            scored_str = "-"
            pct_str = "-"
            grade_str = "-"

        marks_table_data.append([
            Paragraph(str(idx), table_center),
            Paragraph(f"<b>{sched.subject.name}</b>", cell_norm),
            Paragraph(f"{max_m:.0f}", table_center),
            Paragraph(f"{sched.pass_marks:.0f}", table_center),
            Paragraph(scored_str, table_center),
            Paragraph(pct_str, table_center),
            Paragraph(f"<b>{grade_str}</b>", table_center),
            Paragraph(rec.remarks or 'Good', cell_norm),
        ])

    overall_pct = (total_obtained / total_max * 100) if total_max else 0

    # Total Row
    marks_table_data.append([
        Paragraph("", table_center),
        Paragraph("<b>GRAND TOTAL</b>", cell_bold),
        Paragraph(f"<b>{total_max:.0f}</b>", table_center),
        Paragraph("-", table_center),
        Paragraph(f"<font color='#059669'><b>{total_obtained:.1f}</b></font>", table_center),
        Paragraph(f"<b>{overall_pct:.1f}%</b>", table_center),
        Paragraph(f"<b>{calc_grade(overall_pct)}</b>", table_center),
        Paragraph("<b>Pass & Promoted</b>" if overall_pct >= 35 else "<b>Needs Guidance</b>", cell_bold),
    ])

    marks_table = Table(marks_table_data, colWidths=[20, 130, 55, 55, 65, 60, 50, 85])
    marks_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9F1239')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F8F9FC')]),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#EDE9FE')),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(marks_table)
    story.append(Spacer(1, 14))

    # Attendance & Conduct Summary in Report Card
    att_stats = student.get_monthly_attendance_stats()
    att_box_data = [
        [
            Paragraph("<b>Attendance Record:</b>", cell_bold),
            Paragraph(f"Monthly Attendance: <b>{att_stats['percentage']}%</b> ({att_stats['present_days']}/{att_stats['total_days']} working days)", cell_norm),
            Paragraph("<b>Overall Result:</b>", cell_bold),
            Paragraph(f"<font color='#059669'><b>OUTSTANDING ({calc_grade(overall_pct)})</b></font>", cell_bold),
        ]
    ]
    att_table = Table(att_box_data, colWidths=[110, 190, 95, 125])
    att_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(att_table)
    story.append(Spacer(1, 35))

    # Signatures
    sig_data = [
        [
            Paragraph("________________________<br/><b>Class Teacher</b>", sub_title),
            Paragraph("________________________<br/><b>Parent / Guardian</b>", sub_title),
            Paragraph("________________________<br/><b>Principal Seal & Signature</b>", sub_title)
        ]
    ]
    sig_table = Table(sig_data, colWidths=[170, 170, 180])
    story.append(sig_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def calc_grade(pct):
    if pct >= 90: return 'A+'
    elif pct >= 80: return 'A'
    elif pct >= 70: return 'B+'
    elif pct >= 60: return 'B'
    elif pct >= 50: return 'C+'
    elif pct >= 40: return 'C'
    elif pct >= 35: return 'D+'
    else: return 'E'
