import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime

def generate_fee_defaulters_pdf(installment, paid_records, unpaid_students, school_class=None):
    """
    Generates a clean, professional PDF report of students who paid vs pending for an installment.
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

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#9F1239'),
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#475569'),
        alignment=1
    )
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#64748B'),
        alignment=1
    )
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E293B')
    )
    table_hdr_style = ParagraphStyle(
        'TableHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )

    # Header
    story.append(Paragraph("DARUL MA'ARIF WOMEN'S ACADEMY", title_style))
    story.append(Paragraph("Kodampuzha, Kozhikode, Kerala - 673014", subtitle_style))
    story.append(Spacer(1, 4))
    
    class_name = school_class.display_name if school_class else "All Classes"
    due_title = installment.title if installment else "Fee Installment"
    amount_str = f"₹{installment.amount}" if installment else "-"
    due_date_str = installment.due_date.strftime('%d-%b-%Y') if installment else "-"
    
    story.append(Paragraph(f"FEE STATUS & DEFAULTERS REPORT &bull; {due_title}", section_title))
    story.append(Paragraph(f"Class: <b>{class_name}</b> &nbsp;|&nbsp; Due Date: <b>{due_date_str}</b> &nbsp;|&nbsp; Installment Amount: <b>{amount_str}</b> &nbsp;|&nbsp; Generated on: <b>{datetime.now().strftime('%d-%m-%Y %I:%M %p')}</b>", meta_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E25B78'), spaceAfter=14))

    # Summary Statistics Box
    total_due_students = len(paid_records) + len(unpaid_students)
    paid_count = len(paid_records)
    unpaid_count = len(unpaid_students)
    total_collected = sum(r['amount_paid'] for r in paid_records)
    total_pending = unpaid_count * (installment.amount if installment else 0)

    summary_data = [
        [
            Paragraph("<b>Total Target Students:</b>", cell_style), Paragraph(str(total_due_students), cell_style),
            Paragraph("<b>Paid Count:</b>", cell_style), Paragraph(f"<font color='#059669'><b>{paid_count}</b></font>", cell_style),
            Paragraph("<b>Pending (Defaulters):</b>", cell_style), Paragraph(f"<font color='#DC2626'><b>{unpaid_count}</b></font>", cell_style),
        ],
        [
            Paragraph("<b>Total Amount Collected:</b>", cell_style), Paragraph(f"<font color='#059669'><b>₹{total_collected:,.2f}</b></font>", cell_style),
            Paragraph("<b>Total Outstanding Dues:</b>", cell_style), Paragraph(f"<font color='#DC2626'><b>₹{total_pending:,.2f}</b></font>", cell_style),
            Paragraph("<b>Collection Rate:</b>", cell_style), Paragraph(f"<b>{(paid_count/total_due_students*100) if total_due_students else 0:.1f}%</b>", cell_style),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[110, 60, 100, 75, 105, 75])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # SECTION 1: Pending Students (Defaulters)
    story.append(Paragraph(f"<b>1. Fee Defaulters List ({unpaid_count} Pending)</b>", section_title))
    story.append(Spacer(1, 6))

    if unpaid_students:
        defaulters_table_data = [
            [
                Paragraph("#", table_hdr_style),
                Paragraph("Adm No", table_hdr_style),
                Paragraph("Student Name", table_hdr_style),
                Paragraph("Class", table_hdr_style),
                Paragraph("Guardian & Contact", table_hdr_style),
                Paragraph("Amount Due", table_hdr_style),
                Paragraph("Status", table_hdr_style),
            ]
        ]
        for idx, s in enumerate(unpaid_students, 1):
            defaulters_table_data.append([
                Paragraph(str(idx), cell_style),
                Paragraph(s.admission_number, cell_style),
                Paragraph(f"<b>{s.full_name}</b>", cell_style),
                Paragraph(s.current_class.display_name, cell_style),
                Paragraph(f"{s.father_or_guardian_name}<br/>{s.guardian_phone}", cell_style),
                Paragraph(f"<font color='#DC2626'><b>₹{installment.amount:,.2f}</b></font>", cell_style),
                Paragraph("<font color='#DC2626'><b>UNPAID</b></font>", cell_style),
            ])
        def_table = Table(defaulters_table_data, colWidths=[24, 75, 125, 115, 105, 55, 45])
        def_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC2626')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF1F2')]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(def_table)
    else:
        story.append(Paragraph("<font color='#059669'><b>All students have cleared this fee installment!</b></font>", cell_style))

    story.append(Spacer(1, 15))

    # SECTION 2: Paid Students
    story.append(Paragraph(f"<b>2. Cleared / Paid List ({paid_count} Students)</b>", section_title))
    story.append(Spacer(1, 6))

    if paid_records:
        paid_table_data = [
            [
                Paragraph("#", table_hdr_style),
                Paragraph("Receipt No", table_hdr_style),
                Paragraph("Student Name", table_hdr_style),
                Paragraph("Class", table_hdr_style),
                Paragraph("Payment Date", table_hdr_style),
                Paragraph("Mode", table_hdr_style),
                Paragraph("Amount Paid", table_hdr_style),
            ]
        ]
        for idx, p in enumerate(paid_records, 1):
            paid_table_data.append([
                Paragraph(str(idx), cell_style),
                Paragraph(p['receipt_number'], cell_style),
                Paragraph(f"<b>{p['student_name']}</b>", cell_style),
                Paragraph(p['class_name'], cell_style),
                Paragraph(p['payment_date'].strftime('%d-%b-%Y'), cell_style),
                Paragraph(p['payment_mode'], cell_style),
                Paragraph(f"<font color='#059669'><b>₹{p['amount_paid']:,.2f}</b></font>", cell_style),
            ])
        paid_table = Table(paid_table_data, colWidths=[24, 85, 130, 110, 75, 55, 65])
        paid_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0FDF4')]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(paid_table)

    story.append(Spacer(1, 25))
    story.append(Paragraph("This is a computer-generated fee audit report issued by Darul Ma'arif Women's Academy administration.", meta_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_fee_receipt_pdf(payment):
    """
    Generates a printable single payment receipt PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'ReceiptTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#9F1239'),
        alignment=1
    )
    sub_style = ParagraphStyle(
        'ReceiptSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        alignment=1
    )
    cell_bold = ParagraphStyle('CBold', fontName='Helvetica-Bold', fontSize=10, textColor=colors.HexColor('#1E293B'))
    cell_norm = ParagraphStyle('CNorm', fontName='Helvetica', fontSize=10, textColor=colors.HexColor('#334155'))

    story.append(Paragraph("DARUL MA'ARIF WOMEN'S ACADEMY", title_style))
    story.append(Paragraph("Kodampuzha, Kozhikode, Kerala &bull; Ph: +91 98470 12345", sub_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>FEE PAYMENT RECEIPT</b>", ParagraphStyle('R', alignment=1, fontSize=12, fontName='Helvetica-Bold', textColor=colors.HexColor('#059669'))))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#E25B78'), spaceAfter=14))

    # Fee particulars label and detail
    if payment.monthly_vehicle_fee:
        mv = payment.monthly_vehicle_fee
        part_text = f"Monthly Vehicle Fee: {mv.month_name} {mv.year}"
        if mv.bus_stop:
            part_text += f" ({mv.bus_stop.stop_name})"
        if mv.custom_notes:
            part_text += f" - {mv.custom_notes}"
    elif payment.installment:
        part_text = f"{payment.installment.title} ({payment.installment.fee_structure.title})"
    else:
        part_text = payment.get_fee_type_display()

    receipt_meta = [
        [Paragraph("<b>Receipt No:</b>", cell_bold), Paragraph(payment.receipt_number, cell_norm),
         Paragraph("<b>Date:</b>", cell_bold), Paragraph(payment.payment_date.strftime('%d-%b-%Y'), cell_norm)],
        [Paragraph("<b>Student Name:</b>", cell_bold), Paragraph(payment.student.full_name, cell_bold),
         Paragraph("<b>Admission No:</b>", cell_bold), Paragraph(payment.student.admission_number, cell_norm)],
        [Paragraph("<b>Class / Course:</b>", cell_bold), Paragraph(payment.student.current_class.display_name if payment.student.current_class else 'N/A', cell_norm),
         Paragraph("<b>Guardian:</b>", cell_bold), Paragraph(payment.student.father_or_guardian_name, cell_norm)],
        [Paragraph("<b>Fee Particulars:</b>", cell_bold), Paragraph(part_text, cell_bold),
         Paragraph("<b>Payment Mode:</b>", cell_bold), Paragraph(payment.get_payment_mode_display(), cell_norm)],
        [Paragraph("<b>Transaction Ref:</b>", cell_bold), Paragraph(payment.transaction_id or 'N/A', cell_norm),
         Paragraph("<b>Collected By:</b>", cell_bold), Paragraph(payment.collected_by.get_full_name() if payment.collected_by else 'Accounts Desk', cell_norm)],
    ]

    table = Table(receipt_meta, colWidths=[100, 170, 95, 150])
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9FC')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 15))

    amount_box = [
        [Paragraph("<b>AMOUNT RECEIVED:</b>", ParagraphStyle('A1', fontName='Helvetica-Bold', fontSize=12, textColor=colors.HexColor('#065F46'))),
         Paragraph(f"<b>₹{payment.amount_paid:,.2f}</b>", ParagraphStyle('A2', fontName='Helvetica-Bold', fontSize=14, textColor=colors.HexColor('#059669')))]
    ]
    amt_table = Table(amount_box, colWidths=[200, 315])
    amt_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#ECFDF5')),
        ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor('#10B981')),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(amt_table)

    story.append(Spacer(1, 40))
    sig_data = [
        [Paragraph("_______________________<br/><b>Student / Parent Signature</b>", sub_style),
         Paragraph("_______________________<br/><b>Authorized Signatory / Seal</b>", sub_style)]
    ]
    sig_table = Table(sig_data, colWidths=[250, 265])
    story.append(sig_table)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_vehicle_defaulters_pdf(month, year, paid_records, unpaid_dues, bus_stop=None):
    """
    Generates a clean, professional PDF report of Monthly Vehicle Transportation fee
    defaulters and collections for a specific month/year.
    """
    import calendar
    month_name = calendar.month_name[month]
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
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#9F1239'),
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor('#475569'),
        alignment=1
    )
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#64748B'),
        alignment=1
    )
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#1E293B')
    )
    table_hdr_style = ParagraphStyle(
        'TableHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.white
    )
    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#1E293B')
    )

    # Header
    story.append(Paragraph("DARUL MA'ARIF WOMEN'S ACADEMY", title_style))
    story.append(Paragraph("Kodampuzha, Kozhikode, Kerala - 673014", subtitle_style))
    story.append(Spacer(1, 4))

    stop_filter_text = f"Bus Stop: <b>{bus_stop.stop_name}</b>" if bus_stop else "All Academy Bus Routes"
    story.append(Paragraph(f"MONTHLY VEHICLE TRANSPORTATION DUES & DEFAULTERS &bull; {month_name.upper()} {year}", section_title))
    story.append(Paragraph(f"{stop_filter_text} &nbsp;|&nbsp; Billing Period: <b>{month_name} {year}</b> &nbsp;|&nbsp; Generated: <b>{datetime.now().strftime('%d-%m-%Y %I:%M %p')}</b>", meta_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#E25B78'), spaceAfter=14))

    # Summary
    total_opted = len(paid_records) + len(unpaid_dues)
    paid_count = len(paid_records)
    unpaid_count = len(unpaid_dues)
    total_collected = sum(r['amount_paid'] for r in paid_records)
    total_pending = sum(d.final_amount for d in unpaid_dues)

    summary_data = [
        [
            Paragraph("<b>Total Bus Pass Holders:</b>", cell_style), Paragraph(str(total_opted), cell_style),
            Paragraph("<b>Paid Count:</b>", cell_style), Paragraph(f"<font color='#059669'><b>{paid_count}</b></font>", cell_style),
            Paragraph("<b>Pending Defaulters:</b>", cell_style), Paragraph(f"<font color='#DC2626'><b>{unpaid_count}</b></font>", cell_style),
        ],
        [
            Paragraph("<b>Total Amount Collected:</b>", cell_style), Paragraph(f"<font color='#059669'><b>₹{total_collected:,.2f}</b></font>", cell_style),
            Paragraph("<b>Total Outstanding Dues:</b>", cell_style), Paragraph(f"<font color='#DC2626'><b>₹{total_pending:,.2f}</b></font>", cell_style),
            Paragraph("<b>Collection Rate:</b>", cell_style), Paragraph(f"<b>{(paid_count/total_opted*100) if total_opted else 0:.1f}%</b>", cell_style),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[110, 60, 100, 75, 105, 75])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8F9FC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # Unpaid (Defaulters)
    story.append(Paragraph(f"<b>1. Pending Vehicle Dues ({unpaid_count} Defaulters)</b>", section_title))
    story.append(Spacer(1, 6))

    if unpaid_dues:
        def_table_data = [
            [
                Paragraph("#", table_hdr_style),
                Paragraph("Adm No", table_hdr_style),
                Paragraph("Student Name", table_hdr_style),
                Paragraph("Bus Stop", table_hdr_style),
                Paragraph("Base Fee", table_hdr_style),
                Paragraph("Concession / Note", table_hdr_style),
                Paragraph("Net Due (₹)", table_hdr_style),
            ]
        ]
        for idx, d in enumerate(unpaid_dues, 1):
            disc_text = "-"
            if d.custom_discount_type == 'fixed' and d.custom_discount_value > 0:
                disc_text = f"₹{d.custom_discount_value} off"
            elif d.custom_discount_type == 'percent' and d.custom_discount_value > 0:
                disc_text = f"{d.custom_discount_value}% off"
            if d.custom_notes:
                disc_text += f"<br/><font color='#64748B'><i>{d.custom_notes}</i></font>"

            def_table_data.append([
                Paragraph(str(idx), cell_style),
                Paragraph(d.student.admission_number, cell_style),
                Paragraph(f"<b>{d.student.full_name}</b><br/><font color='#64748B'>{d.student.current_class.display_name if d.student.current_class else ''}</font>", cell_style),
                Paragraph(d.bus_stop.stop_name if d.bus_stop else "—", cell_style),
                Paragraph(f"₹{d.base_fee:,.2f}", cell_style),
                Paragraph(disc_text, cell_style),
                Paragraph(f"<font color='#DC2626'><b>₹{d.final_amount:,.2f}</b></font>", cell_style),
            ])
        dtable = Table(def_table_data, colWidths=[24, 65, 130, 110, 60, 100, 65])
        dtable.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#DC2626')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#FFF1F2')]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(dtable)
    else:
        story.append(Paragraph("<font color='#059669'><b>All students have cleared vehicle fees for this month!</b></font>", cell_style))

    story.append(Spacer(1, 15))

    # Paid
    story.append(Paragraph(f"<b>2. Cleared Vehicle Payments ({paid_count} Paid)</b>", section_title))
    story.append(Spacer(1, 6))

    if paid_records:
        paid_table_data = [
            [
                Paragraph("#", table_hdr_style),
                Paragraph("Receipt No", table_hdr_style),
                Paragraph("Student Name", table_hdr_style),
                Paragraph("Bus Stop", table_hdr_style),
                Paragraph("Payment Date", table_hdr_style),
                Paragraph("Mode", table_hdr_style),
                Paragraph("Amount Paid", table_hdr_style),
            ]
        ]
        for idx, p in enumerate(paid_records, 1):
            paid_table_data.append([
                Paragraph(str(idx), cell_style),
                Paragraph(p['receipt_number'], cell_style),
                Paragraph(f"<b>{p['student_name']}</b>", cell_style),
                Paragraph(p.get('bus_stop_name', '—'), cell_style),
                Paragraph(p['payment_date'].strftime('%d-%b-%Y'), cell_style),
                Paragraph(p['payment_mode'], cell_style),
                Paragraph(f"<font color='#059669'><b>₹{p['amount_paid']:,.2f}</b></font>", cell_style),
            ])
        ptable = Table(paid_table_data, colWidths=[24, 85, 120, 110, 75, 55, 70])
        ptable.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0FDF4')]),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(ptable)

    story.append(Spacer(1, 25))
    story.append(Paragraph("This is an official computer-generated transportation fee audit report issued by Darul Ma'arif Women's Academy.", meta_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

