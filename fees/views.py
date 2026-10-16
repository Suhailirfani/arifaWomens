from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Sum, Count, Q
from decimal import Decimal
from datetime import date

import calendar
from .models import (
    FeeCategory, FeeStructure, FeeInstallment, StudentFeePayment, auto_sync_due_installments,
    BusStop, StudentVehiclePass, VehicleBillingSetting, StudentMonthlyVehicleFee, generate_monthly_vehicle_dues
)
from .forms import (
    FeePaymentForm, FeeCategoryForm, FeeStructureForm, FeeInstallmentForm,
    BusStopForm, StudentVehiclePassForm, StudentMonthlyVehicleFeeCustomForm, VehicleBillingSettingForm
)
from .pdf_utils import generate_fee_defaulters_pdf, generate_fee_receipt_pdf, generate_vehicle_defaulters_pdf
from academics.models import SchoolClass, AcademicYear, GradeLevel
from students.models import Student

@login_required
def fee_dashboard(request):
    """
    Fee dashboard for admin and staff.
    """
    # Automatically synchronize active due targets according to calendar date
    auto_sync_due_installments()

    today = date.today()
    current_ay = AcademicYear.objects.filter(is_current=True).first()

    # Total collected all-time
    total_collected = StudentFeePayment.objects.aggregate(tot=Sum('amount_paid'))['tot'] or Decimal('0.00')

    # Total collected this month
    this_month_collected = StudentFeePayment.objects.filter(
        payment_date__year=today.year,
        payment_date__month=today.month
    ).aggregate(tot=Sum('amount_paid'))['tot'] or Decimal('0.00')

    # Active due installment
    current_installment = FeeInstallment.objects.filter(is_current_due=True).first()
    if not current_installment:
        current_installment = FeeInstallment.objects.order_by('due_date').first()

    paid_count = 0
    unpaid_count = 0
    total_due_amount = Decimal('0.00')
    collected_due_amount = Decimal('0.00')

    if current_installment:
        eligible_students = Student.objects.filter(is_active=True)
        if current_installment.fee_structure.school_class:
            eligible_students = eligible_students.filter(current_class=current_installment.fee_structure.school_class)
        elif current_installment.fee_structure.grade:
            eligible_students = eligible_students.filter(current_class__grade=current_installment.fee_structure.grade)
        if current_installment.requires_vehicle:
            eligible_students = eligible_students.filter(vehicle_opted=True)

        paid_student_ids = StudentFeePayment.objects.filter(installment=current_installment).values_list('student_id', flat=True)
        paid_count = len(paid_student_ids)
        unpaid_count = eligible_students.exclude(id__in=paid_student_ids).count()
        collected_due_amount = StudentFeePayment.objects.filter(installment=current_installment).aggregate(tot=Sum('amount_paid'))['tot'] or Decimal('0.00')
        total_due_amount = unpaid_count * current_installment.amount

    # Class-wise overview
    classes = SchoolClass.objects.all()
    class_fee_stats = []
    for sc in classes:
        sc_students = sc.students.filter(is_active=True)
        sc_payments = StudentFeePayment.objects.filter(student__in=sc_students)
        sc_col = sc_payments.aggregate(tot=Sum('amount_paid'))['tot'] or Decimal('0.00')
        class_fee_stats.append({
            'school_class': sc,
            'students_count': sc_students.count(),
            'total_collected': sc_col
        })

    # Recent payments
    recent_payments = StudentFeePayment.objects.select_related('student__current_class', 'installment').order_by('-payment_date', '-created_at')[:10]

    context = {
        'total_collected': total_collected,
        'this_month_collected': this_month_collected,
        'current_installment': current_installment,
        'paid_count': paid_count,
        'unpaid_count': unpaid_count,
        'total_due_amount': total_due_amount,
        'collected_due_amount': collected_due_amount,
        'class_fee_stats': class_fee_stats,
        'recent_payments': recent_payments,
    }
    return render(request, 'fees/fee_dashboard.html', context)


@login_required
def fee_defaulters_list(request):
    """
    Shows list of students who paid and who NOT paid the active/selected fee installment.
    Provides filter by installment and class, with PDF export.
    """
    installments = FeeInstallment.objects.select_related('fee_structure__category', 'fee_structure__school_class').order_by('-is_current_due', '-due_date')
    classes = SchoolClass.objects.all()

    installment_id = request.GET.get('installment_id')
    class_id = request.GET.get('class_id')

    selected_installment = None
    if installment_id:
        selected_installment = FeeInstallment.objects.filter(id=installment_id).first()
    if not selected_installment:
        selected_installment = FeeInstallment.objects.filter(is_current_due=True).first()
    if not selected_installment and installments.exists():
        selected_installment = installments.first()

    selected_class = None
    if class_id:
        selected_class = SchoolClass.objects.filter(id=class_id).first()

    paid_records = []
    unpaid_students = []
    total_target = 0
    collection_rate = 0.0

    if selected_installment:
        eligible_students = Student.objects.filter(is_active=True).select_related('current_class')
        if selected_installment.fee_structure.school_class:
            eligible_students = eligible_students.filter(current_class=selected_installment.fee_structure.school_class)
        elif selected_installment.fee_structure.grade:
            eligible_students = eligible_students.filter(current_class__grade=selected_installment.fee_structure.grade)

        if selected_installment.requires_vehicle:
            eligible_students = eligible_students.filter(vehicle_opted=True)

        if selected_class:
            eligible_students = eligible_students.filter(current_class=selected_class)

        # Paid records
        payments = StudentFeePayment.objects.filter(installment=selected_installment, student__in=eligible_students).select_related('student__current_class')
        paid_student_ids = payments.values_list('student_id', flat=True)

        for p in payments:
            paid_records.append({
                'receipt_number': p.receipt_number,
                'student_name': p.student.full_name,
                'student_id': p.student.id,
                'class_name': p.student.current_class.display_name,
                'payment_date': p.payment_date,
                'payment_mode': p.get_payment_mode_display(),
                'amount_paid': p.amount_paid,
                'guardian_phone': p.student.guardian_phone
            })

        unpaid_students = eligible_students.exclude(id__in=paid_student_ids).order_by('current_class', 'roll_number', 'full_name')

        total_target = len(paid_records) + len(unpaid_students)
        if total_target > 0:
            collection_rate = round((len(paid_records) / total_target * 100), 1)

    context = {
        'installments': installments,
        'classes': classes,
        'selected_installment': selected_installment,
        'selected_class': selected_class,
        'paid_records': paid_records,
        'unpaid_students': unpaid_students,
        'total_target': total_target,
        'collection_rate': collection_rate,
        'total_pending_amount': len(unpaid_students) * (selected_installment.amount if selected_installment else Decimal('0.00')),
        'total_collected_amount': sum(r['amount_paid'] for r in paid_records)
    }
    return render(request, 'fees/fee_defaulters_list.html', context)


@login_required
def download_defaulters_pdf(request):
    """
    Downloads fee status and defaulters report as a formatted PDF.
    """
    installment_id = request.GET.get('installment_id')
    class_id = request.GET.get('class_id')

    installment = None
    if installment_id:
        installment = FeeInstallment.objects.filter(id=installment_id).first()
    if not installment:
        installment = FeeInstallment.objects.filter(is_current_due=True).first()
    if not installment:
        installment = FeeInstallment.objects.first()

    selected_class = None
    if class_id:
        selected_class = SchoolClass.objects.filter(id=class_id).first()

    eligible_students = Student.objects.filter(is_active=True).select_related('current_class')
    if installment and installment.fee_structure.school_class:
        eligible_students = eligible_students.filter(current_class=installment.fee_structure.school_class)
    elif installment and installment.fee_structure.grade:
        eligible_students = eligible_students.filter(current_class__grade=installment.fee_structure.grade)

    if installment and installment.requires_vehicle:
        eligible_students = eligible_students.filter(vehicle_opted=True)

    if selected_class:
        eligible_students = eligible_students.filter(current_class=selected_class)

    payments = StudentFeePayment.objects.filter(installment=installment, student__in=eligible_students).select_related('student__current_class')
    paid_student_ids = payments.values_list('student_id', flat=True)

    paid_records = []
    for p in payments:
        paid_records.append({
            'receipt_number': p.receipt_number,
            'student_name': p.student.full_name,
            'class_name': p.student.current_class.display_name,
            'payment_date': p.payment_date,
            'payment_mode': p.get_payment_mode_display(),
            'amount_paid': p.amount_paid
        })

    unpaid_students = list(eligible_students.exclude(id__in=paid_student_ids).order_by('current_class', 'roll_number', 'full_name'))

    pdf_data = generate_fee_defaulters_pdf(installment, paid_records, unpaid_students, selected_class)
    response = HttpResponse(pdf_data, content_type='application/pdf')
    inst_title = installment.title.replace(' ', '_') if installment else 'Fee_Defaulters'
    response['Content-Disposition'] = f'attachment; filename="Darul_Maarif_Fee_Defaulters_{inst_title}.pdf"'
    return response


@login_required
def fee_collect(request):
    """
    Form to record fee payment for a student (Course Fee Installment or Monthly Vehicle Fee).
    """
    if request.method == 'POST':
        form = FeePaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.collected_by = request.user
            payment.save()

            # If vehicle monthly fee was paid, update the due record
            if payment.fee_type == StudentFeePayment.FeeType.VEHICLE_MONTHLY and payment.monthly_vehicle_fee:
                mv = payment.monthly_vehicle_fee
                mv.is_paid = True
                mv.paid_date = payment.payment_date
                mv.save()

            messages.success(request, f"Fee payment of ₹{payment.amount_paid} recorded for {payment.student.full_name}. Receipt: {payment.receipt_number}")
            return redirect('fees:receipt_detail', receipt_number=payment.receipt_number)
    else:
        student_id = request.GET.get('student_id')
        installment_id = request.GET.get('installment_id')
        vehicle_fee_id = request.GET.get('vehicle_fee_id')
        fee_type = request.GET.get('fee_type')

        initial_data = {}
        if student_id:
            initial_data['student'] = student_id

        if vehicle_fee_id:
            mv_fee = StudentMonthlyVehicleFee.objects.filter(id=vehicle_fee_id).first()
            if mv_fee:
                initial_data['student'] = mv_fee.student_id
                initial_data['fee_type'] = StudentFeePayment.FeeType.VEHICLE_MONTHLY
                initial_data['monthly_vehicle_fee'] = mv_fee.id
                initial_data['amount_paid'] = mv_fee.final_amount
        elif installment_id:
            inst = FeeInstallment.objects.filter(id=installment_id).first()
            if inst:
                initial_data['fee_type'] = StudentFeePayment.FeeType.INSTALLMENT
                initial_data['installment'] = inst.id
                initial_data['amount_paid'] = inst.amount
        elif fee_type:
            initial_data['fee_type'] = fee_type
        else:
            initial_data['fee_type'] = StudentFeePayment.FeeType.INSTALLMENT

        form = FeePaymentForm(initial=initial_data)

    pending_vehicle_dues = StudentMonthlyVehicleFee.objects.filter(is_paid=False).select_related('student', 'bus_stop')
    installments = FeeInstallment.objects.select_related('fee_structure').order_by('due_date')

    context = {
        'form': form,
        'pending_vehicle_dues': pending_vehicle_dues,
        'installments': installments,
    }
    return render(request, 'fees/fee_collect.html', context)


@login_required
def receipt_detail(request, receipt_number):
    """
    Shows receipt details with printable view.
    """
    payment = get_object_or_404(
        StudentFeePayment.objects.select_related(
            'student__current_class', 'installment__fee_structure', 'monthly_vehicle_fee__bus_stop', 'collected_by'
        ),
        receipt_number=receipt_number
    )
    return render(request, 'fees/receipt_detail.html', {'payment': payment})


@login_required
def receipt_pdf(request, receipt_number):
    """
    Downloads receipt as PDF.
    """
    payment = get_object_or_404(
        StudentFeePayment.objects.select_related('student__current_class', 'installment__fee_structure', 'monthly_vehicle_fee__bus_stop', 'collected_by'),
        receipt_number=receipt_number
    )
    pdf_content = generate_fee_receipt_pdf(payment)
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Receipt_{payment.receipt_number}.pdf"'
    return response


@login_required
def fee_master(request):
    """
    Fee Master central setup:
    View all fee structures, installment breakdown, fee categories, and bus stop vehicle fees.
    Automatically keeps active due installments synced with the calendar date.
    """
    auto_sync_due_installments()

    structures = FeeStructure.objects.select_related(
        'category', 'school_class', 'grade', 'academic_year'
    ).prefetch_related('installments').order_by('-academic_year__start_date', 'title')
    
    categories = FeeCategory.objects.prefetch_related('structures').all()
    installments = FeeInstallment.objects.select_related('fee_structure').order_by('due_date')
    current_due_inst = FeeInstallment.objects.filter(is_current_due=True).first()

    # Vehicle transportation master summary
    bus_stops = BusStop.objects.all().order_by('route_name', 'stop_name')
    vehicle_setting = VehicleBillingSetting.objects.first()
    if not vehicle_setting:
        vehicle_setting = VehicleBillingSetting.objects.create(due_day_of_month=1, auto_generate=True)
    
    active_vehicle_passes = StudentVehiclePass.objects.filter(is_active=True).select_related('student__current_class', 'bus_stop')
    today = date.today()
    month_vehicle_dues = StudentMonthlyVehicleFee.objects.filter(month=today.month, year=today.year)

    context = {
        'structures': structures,
        'categories': categories,
        'installments': installments,
        'current_due_inst': current_due_inst,
        'total_structures': structures.count(),
        'total_installments': installments.count(),
        'bus_stops': bus_stops,
        'vehicle_setting': vehicle_setting,
        'active_vehicle_passes': active_vehicle_passes,
        'active_vehicle_passes_count': active_vehicle_passes.count(),
        'month_vehicle_dues_count': month_vehicle_dues.count(),
        'current_month_name': calendar.month_name[today.month],
        'current_year': today.year,
    }
    return render(request, 'fees/fee_master.html', context)


@login_required
def fee_structure_builder(request, pk=None):
    """
    Interactive Installment Plan Builder:
    Configure annual fee structures, specify how many installments it has,
    what amount will be paid in each installment, and their due dates.
    All without needing Django Admin!
    """
    structure = get_object_or_404(FeeStructure, pk=pk) if pk else None
    categories = FeeCategory.objects.all()
    academic_years = AcademicYear.objects.all().order_by('-start_date')
    school_classes = SchoolClass.objects.all().select_related('grade', 'course', 'academic_year')
    grades = GradeLevel.objects.all().order_by('sequence')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        category_id = request.POST.get('category')
        academic_year_id = request.POST.get('academic_year')
        school_class_id = request.POST.get('school_class') or None
        grade_id = request.POST.get('grade') or None
        total_amount_str = request.POST.get('total_amount', '0').strip()
        description = request.POST.get('description', '').strip()

        try:
            total_amount = Decimal(total_amount_str)
        except Exception:
            total_amount = Decimal('0.00')

        if not title:
            messages.error(request, "Fee Plan Title is required.")
            return redirect(request.path)

        if not category_id or not academic_year_id:
            messages.error(request, "Please select both a Fee Category and an Academic Year.")
            return redirect(request.path)

        category = get_object_or_404(FeeCategory, pk=category_id)
        academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)
        school_class = SchoolClass.objects.filter(pk=school_class_id).first() if school_class_id else None
        grade = GradeLevel.objects.filter(pk=grade_id).first() if grade_id else None

        if structure:
            structure.title = title
            structure.category = category
            structure.academic_year = academic_year
            structure.school_class = school_class
            structure.grade = grade
            structure.total_amount = total_amount
            structure.description = description
            structure.save()
        else:
            structure = FeeStructure.objects.create(
                title=title,
                category=category,
                academic_year=academic_year,
                school_class=school_class,
                grade=grade,
                total_amount=total_amount,
                description=description
            )

        # Process submitted installment rows
        inst_ids = request.POST.getlist('inst_id')
        inst_numbers = request.POST.getlist('inst_number')
        inst_titles = request.POST.getlist('inst_title')
        inst_amounts = request.POST.getlist('inst_amount')
        inst_due_dates = request.POST.getlist('inst_due_date')
        inst_vehicles = request.POST.getlist('inst_requires_vehicle')

        submitted_ids = [int(i) for i in inst_ids if i and i.isdigit()]

        # Safely remove installments that were deleted in the builder
        existing_installments = structure.installments.all()
        for old_inst in existing_installments:
            if old_inst.id not in submitted_ids:
                if old_inst.payments.exists():
                    messages.warning(request, f"Installment '{old_inst.title}' could not be deleted because payments have already been collected against it.")
                else:
                    old_inst.delete()

        # Update or create installments
        num_saved = 0
        for i in range(len(inst_titles)):
            row_title = inst_titles[i].strip() if i < len(inst_titles) else ''
            if not row_title:
                continue

            row_id = int(inst_ids[i]) if (i < len(inst_ids) and inst_ids[i] and inst_ids[i].isdigit()) else None
            row_num = int(inst_numbers[i]) if (i < len(inst_numbers) and inst_numbers[i] and inst_numbers[i].isdigit()) else (i + 1)
            
            try:
                row_amount = Decimal(inst_amounts[i].strip()) if i < len(inst_amounts) else Decimal('0.00')
            except Exception:
                row_amount = Decimal('0.00')

            row_date_str = inst_due_dates[i].strip() if i < len(inst_due_dates) else ''
            try:
                row_due_date = date.fromisoformat(row_date_str) if row_date_str else date.today()
            except Exception:
                row_due_date = date.today()

            row_vehicle = (i < len(inst_vehicles) and inst_vehicles[i] in ['1', 'true', 'on'])

            if row_id:
                inst_obj = FeeInstallment.objects.filter(id=row_id, fee_structure=structure).first()
                if inst_obj:
                    inst_obj.installment_number = row_num
                    inst_obj.title = row_title
                    inst_obj.amount = row_amount
                    inst_obj.due_date = row_due_date
                    inst_obj.requires_vehicle = row_vehicle
                    inst_obj.save()
                    num_saved += 1
            else:
                FeeInstallment.objects.create(
                    fee_structure=structure,
                    installment_number=row_num,
                    title=row_title,
                    amount=row_amount,
                    due_date=row_due_date,
                    requires_vehicle=row_vehicle
                )
                num_saved += 1

        # Automatically synchronize which installment is next due by calendar date
        auto_sync_due_installments()

        messages.success(request, f"Fee Structure '{structure.title}' and {num_saved} installment(s) saved successfully! Next due date synchronized.")
        return redirect('fees:fee_master')

    existing_installments = list(structure.installments.order_by('installment_number', 'due_date')) if structure else []

    context = {
        'structure': structure,
        'categories': categories,
        'academic_years': academic_years,
        'school_classes': school_classes,
        'grades': grades,
        'existing_installments': existing_installments,
        'title': f"Edit Installment Plan: {structure.title}" if structure else "Annual Fee Structure & Installment Builder",
        'is_edit': bool(structure)
    }
    return render(request, 'fees/fee_structure_builder.html', context)


@login_required
def fee_auto_sync_dues(request):
    """
    Manually trigger an auto-synchronization of all active due installments
    based on the current calendar date.
    """
    auto_sync_due_installments()
    messages.success(request, "Active installment dues successfully synchronized with the current calendar date! Defaulter trackers updated.")
    next_url = request.META.get('HTTP_REFERER') or 'fees:fee_master'
    return redirect(next_url)


@login_required
def fee_structure_delete(request, pk):
    """Safely delete a fee structure if no payments exist."""
    structure = get_object_or_404(FeeStructure, pk=pk)
    has_payments = StudentFeePayment.objects.filter(installment__fee_structure=structure).exists()
    if has_payments:
        messages.error(request, f"Cannot delete '{structure.title}' because student fee receipts have already been issued against it.")
        return redirect('fees:fee_master')
    
    if request.method == 'POST':
        title = structure.title
        structure.delete()
        auto_sync_due_installments()
        messages.success(request, f"Fee structure '{title}' and its installment plan were successfully deleted.")
        return redirect('fees:fee_master')
    
    return render(request, 'fees/confirm_delete.html', {
        'object_type': 'Fee Structure',
        'object_name': structure.title,
        'cancel_url': 'fees:fee_master',
        'warning': 'Deleting this fee structure will permanently remove all of its uncollected installments.'
    })


@login_required
def fee_installment_delete(request, pk):
    """Safely delete a single installment if no payments exist."""
    installment = get_object_or_404(FeeInstallment, pk=pk)
    if installment.payments.exists():
        messages.error(request, f"Cannot delete '{installment.title}' because fee receipts have already been issued against it.")
        return redirect('fees:fee_master')

    if request.method == 'POST':
        title = installment.title
        structure_title = installment.fee_structure.title
        installment.delete()
        auto_sync_due_installments()
        messages.success(request, f"Installment '{title}' deleted from '{structure_title}'.")
        return redirect('fees:fee_master')

    return render(request, 'fees/confirm_delete.html', {
        'object_type': 'Installment',
        'object_name': f"{installment.title} (₹{installment.amount})",
        'cancel_url': 'fees:fee_master',
        'warning': 'Are you sure you want to delete this installment from the fee plan?'
    })


@login_required
def fee_structure_create(request):
    """Redirect to the unified builder."""
    return redirect('fees:fee_structure_builder')


@login_required
def fee_structure_edit(request, pk):
    """Redirect to the unified builder."""
    return redirect('fees:fee_structure_builder_edit', pk=pk)


@login_required
def fee_installment_create(request):
    """Add a single installment under a fee structure."""
    structure_id = request.GET.get('structure_id')
    initial_data = {}
    if structure_id:
        initial_data['fee_structure'] = structure_id

    if request.method == 'POST':
        form = FeeInstallmentForm(request.POST)
        if form.is_valid():
            installment = form.save()
            auto_sync_due_installments()
            messages.success(request, f"Installment '{installment.title}' added successfully!")
            return redirect('fees:fee_master')
    else:
        form = FeeInstallmentForm(initial=initial_data)
    return render(request, 'fees/fee_installment_form.html', {'form': form, 'title': 'Add Fee Installment'})


@login_required
def fee_installment_edit(request, pk):
    """Edit an existing installment."""
    installment = get_object_or_404(FeeInstallment, pk=pk)
    if request.method == 'POST':
        form = FeeInstallmentForm(request.POST, instance=installment)
        if form.is_valid():
            form.save()
            auto_sync_due_installments()
            messages.success(request, f"Installment '{installment.title}' updated successfully!")
            return redirect('fees:fee_master')
    else:
        form = FeeInstallmentForm(instance=installment)
    return render(request, 'fees/fee_installment_form.html', {'form': form, 'title': f'Edit Installment: {installment.title}', 'installment': installment})


@login_required
def fee_installment_set_active(request, pk):
    """Quick 1-click action to set an installment as the current active due installment."""
    installment = get_object_or_404(FeeInstallment, pk=pk)
    installment.is_current_due = True
    installment.save()
    messages.success(request, f"'{installment.title}' is now set as the active due installment!")
    return redirect('fees:fee_master')


@login_required
def fee_category_create(request):
    """Create a new fee category."""
    if request.method == 'POST':
        form = FeeCategoryForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Fee Category '{cat.name}' created successfully!")
            return redirect('fees:fee_master')
    else:
        form = FeeCategoryForm()
    return render(request, 'fees/fee_category_form.html', {'form': form, 'title': 'Create Fee Category'})


# =========================================================================
# VEHICLE TRANSPORTATION MONTHLY FEE & BUS STOP MANAGEMENT
# =========================================================================

@login_required
def vehicle_fee_dashboard(request):
    """
    Central vehicle fee & bus stop transport management:
    - View and filter monthly dues for any month / year
    - See unpaid defaulters and paid records
    - Admin can customize partial usage (exact ₹ or % discount)
    - View and manage bus stops and assigned students
    - Configure billing due date (1st or user-determined date)
    """
    today = date.today()
    
    # Month and Year filter
    try:
        month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        month = today.month

    try:
        year = int(request.GET.get('year', today.year))
    except (ValueError, TypeError):
        year = today.year

    bus_stop_id = request.GET.get('bus_stop_id')

    # Ensure billing setting exists
    setting = VehicleBillingSetting.objects.first()
    if not setting:
        setting = VehicleBillingSetting.objects.create(due_day_of_month=1, auto_generate=True)

    # Auto-generate or sync dues for this month/year if active passes exist
    if setting.auto_generate and StudentVehiclePass.objects.filter(is_active=True).exists():
        if not StudentMonthlyVehicleFee.objects.filter(month=month, year=year).exists():
            generate_monthly_vehicle_dues(year=year, month=month, due_day=setting.due_day_of_month)

    # All bus stops with student count
    bus_stops = BusStop.objects.annotate(
        assigned_count=Count('student_passes', filter=Q(student_passes__is_active=True))
    ).order_by('route_name', 'stop_name')

    # All student passes
    passes = StudentVehiclePass.objects.select_related('student__current_class', 'bus_stop').order_by('bus_stop', 'student__full_name')

    # Monthly fee records for the selected month/year
    month_dues_qs = StudentMonthlyVehicleFee.objects.filter(
        month=month, year=year
    ).select_related('student__current_class', 'bus_stop')

    selected_stop = None
    if bus_stop_id:
        selected_stop = BusStop.objects.filter(id=bus_stop_id).first()
        if selected_stop:
            month_dues_qs = month_dues_qs.filter(bus_stop=selected_stop)

    unpaid_dues = list(month_dues_qs.filter(is_paid=False).order_by('bus_stop__stop_name', 'student__full_name'))
    paid_dues = list(month_dues_qs.filter(is_paid=True).order_by('-paid_date', 'student__full_name'))

    # Payments details for paid dues
    paid_records = []
    paid_payments = StudentFeePayment.objects.filter(
        fee_type=StudentFeePayment.FeeType.VEHICLE_MONTHLY,
        monthly_vehicle_fee__in=month_dues_qs.filter(is_paid=True)
    ).select_related('student__current_class', 'monthly_vehicle_fee__bus_stop')
    
    for p in paid_payments:
        paid_records.append({
            'receipt_number': p.receipt_number,
            'student_name': p.student.full_name,
            'bus_stop_name': p.monthly_vehicle_fee.bus_stop.stop_name if p.monthly_vehicle_fee and p.monthly_vehicle_fee.bus_stop else '—',
            'payment_date': p.payment_date,
            'payment_mode': p.get_payment_mode_display(),
            'amount_paid': p.amount_paid,
            'due_obj': p.monthly_vehicle_fee,
        })

    # Summary metrics
    total_opted = len(unpaid_dues) + len(paid_dues)
    expected_amount = sum(d.final_amount for d in month_dues_qs)
    collected_amount = sum(r['amount_paid'] for r in paid_records) if paid_records else sum(d.final_amount for d in paid_dues)
    pending_amount = sum(d.final_amount for d in unpaid_dues)
    collection_rate = round((len(paid_dues) / total_opted * 100), 1) if total_opted > 0 else 0.0

    # Month and Year choices for dropdown
    month_choices = [(i, calendar.month_name[i]) for i in range(1, 13)]
    year_choices = [today.year - 1, today.year, today.year + 1]

    context = {
        'month': month,
        'year': year,
        'month_name': calendar.month_name[month],
        'month_choices': month_choices,
        'year_choices': year_choices,
        'bus_stops': bus_stops,
        'selected_stop': selected_stop,
        'passes': passes,
        'unpaid_dues': unpaid_dues,
        'paid_dues': paid_dues,
        'paid_records': paid_records,
        'total_opted': total_opted,
        'expected_amount': expected_amount,
        'collected_amount': collected_amount,
        'pending_amount': pending_amount,
        'collection_rate': collection_rate,
        'setting': setting,
    }
    return render(request, 'fees/vehicle_dashboard.html', context)


@login_required
def bus_stop_create(request):
    """Add a new bus stop with its fixed monthly fee."""
    if request.method == 'POST':
        form = BusStopForm(request.POST)
        if form.is_valid():
            stop = form.save()
            messages.success(request, f"Bus Stop '{stop.stop_name}' (₹{stop.monthly_fee}/month) created successfully!")
            return redirect('fees:vehicle_fee_dashboard')
    else:
        form = BusStopForm()
    return render(request, 'fees/bus_stop_form.html', {'form': form, 'title': 'Add New Bus Stop'})


@login_required
def bus_stop_edit(request, pk):
    """Edit bus stop details and monthly fee."""
    stop = get_object_or_404(BusStop, pk=pk)
    if request.method == 'POST':
        form = BusStopForm(request.POST, instance=stop)
        if form.is_valid():
            stop = form.save()
            messages.success(request, f"Bus Stop '{stop.stop_name}' updated successfully!")
            return redirect('fees:vehicle_fee_dashboard')
    else:
        form = BusStopForm(instance=stop)
    return render(request, 'fees/bus_stop_form.html', {'form': form, 'title': f'Edit Bus Stop: {stop.stop_name}', 'stop': stop})


@login_required
def bus_stop_delete(request, pk):
    """Safely delete a bus stop if no active passes exist."""
    stop = get_object_or_404(BusStop, pk=pk)
    if stop.student_passes.exists():
        messages.error(request, f"Cannot delete '{stop.stop_name}' because students are currently assigned to this bus stop.")
        return redirect('fees:vehicle_fee_dashboard')

    if request.method == 'POST':
        name = stop.stop_name
        stop.delete()
        messages.success(request, f"Bus stop '{name}' was deleted.")
        return redirect('fees:vehicle_fee_dashboard')

    return render(request, 'fees/confirm_delete.html', {
        'object_type': 'Bus Stop',
        'object_name': f"{stop.stop_name} (₹{stop.monthly_fee}/mo)",
        'cancel_url': 'fees:vehicle_fee_dashboard',
        'warning': 'Are you sure you want to delete this bus stop?'
    })


@login_required
def vehicle_pass_create(request):
    """Assign a student to a Bus Stop with optional standing concession (partial usage discount)."""
    student_id = request.GET.get('student_id')
    initial_data = {}
    if student_id:
        initial_data['student'] = student_id

    if request.method == 'POST':
        form = StudentVehiclePassForm(request.POST)
        if form.is_valid():
            vpass = form.save()
            # Also ensure student.vehicle_opted is True
            student = vpass.student
            if not student.vehicle_opted:
                student.vehicle_opted = True
                student.save(update_fields=['vehicle_opted'])

            # Automatically sync current month's due if unpaid
            today = date.today()
            generate_monthly_vehicle_dues(year=today.year, month=today.month)

            messages.success(
                request,
                f"Bus pass issued for {vpass.student.full_name} ({vpass.bus_stop.stop_name} - Effective: ₹{vpass.calculated_monthly_fee}/mo)!"
            )
            return redirect('fees:vehicle_fee_dashboard')
    else:
        form = StudentVehiclePassForm(initial=initial_data)
    return render(request, 'fees/vehicle_pass_form.html', {'form': form, 'title': 'Assign Student Bus Stop Pass'})


@login_required
def vehicle_pass_edit(request, pk):
    """Edit student bus stop assignment or standing concession."""
    vpass = get_object_or_404(StudentVehiclePass, pk=pk)
    if request.method == 'POST':
        form = StudentVehiclePassForm(request.POST, instance=vpass)
        if form.is_valid():
            vpass = form.save()
            today = date.today()
            generate_monthly_vehicle_dues(year=today.year, month=today.month)
            messages.success(request, f"Bus pass updated for {vpass.student.full_name} (Effective: ₹{vpass.calculated_monthly_fee}/mo)!")
            return redirect('fees:vehicle_fee_dashboard')
    else:
        form = StudentVehiclePassForm(instance=vpass)
    return render(request, 'fees/vehicle_pass_form.html', {'form': form, 'title': f'Edit Bus Pass: {vpass.student.full_name}', 'vpass': vpass})


@login_required
def vehicle_pass_delete(request, pk):
    """Deactivate or remove a student vehicle pass."""
    vpass = get_object_or_404(StudentVehiclePass, pk=pk)
    if request.method == 'POST':
        student_name = vpass.student.full_name
        student = vpass.student
        student.vehicle_opted = False
        student.save(update_fields=['vehicle_opted'])
        vpass.delete()
        messages.success(request, f"Bus pass for '{student_name}' has been cancelled.")
        return redirect('fees:vehicle_fee_dashboard')

    return render(request, 'fees/confirm_delete.html', {
        'object_type': 'Student Vehicle Pass',
        'object_name': f"{vpass.student.full_name} ({vpass.bus_stop.stop_name})",
        'cancel_url': 'fees:vehicle_fee_dashboard',
        'warning': 'Removing this pass will stop monthly vehicle fee charges for this student.'
    })


@login_required
def vehicle_fee_customize(request, pk):
    """
    ADMIN CUSTOMIZATION FOR PARTIAL USAGE IN A GIVEN MONTH:
    Admin can customize a student's vehicle fee in the case of partial usage:
    - Either by reducing the exact amount in a month (₹)
    - Or reducing percentage of charge (%)
    - Adding custom reason (e.g. 10 days usage, medical leave, exam break)
    """
    due_record = get_object_or_404(
        StudentMonthlyVehicleFee.objects.select_related('student__current_class', 'bus_stop'),
        pk=pk
    )

    if request.method == 'POST':
        form = StudentMonthlyVehicleFeeCustomForm(request.POST, instance=due_record)
        if form.is_valid():
            custom_due = form.save(commit=False)
            
            # Recalculate final amount based on discount type and value
            base = custom_due.base_fee
            dtype = custom_due.custom_discount_type
            dval = custom_due.custom_discount_value or Decimal('0.00')

            if dtype == StudentVehiclePass.DiscountType.FIXED:
                custom_due.final_amount = max(Decimal('0.00'), base - dval)
            elif dtype == StudentVehiclePass.DiscountType.PERCENTAGE:
                pct = min(Decimal('100.00'), max(Decimal('0.00'), dval))
                custom_due.final_amount = max(Decimal('0.00'), base * (Decimal('1.00') - (pct / Decimal('100.00'))))
            else:
                custom_due.final_amount = base

            custom_due.save()
            messages.success(
                request,
                f"Customized vehicle fee for {custom_due.student.full_name} ({custom_due.month_name} {custom_due.year}): Final amount set to ₹{custom_due.final_amount}!"
            )
            return redirect(f"/fees/vehicle/?month={custom_due.month}&year={custom_due.year}")
    else:
        form = StudentMonthlyVehicleFeeCustomForm(instance=due_record)

    context = {
        'form': form,
        'due_record': due_record,
        'month_name': due_record.month_name,
        'base_fee': due_record.base_fee,
    }
    return render(request, 'fees/vehicle_month_customize.html', context)


@login_required
def vehicle_dues_generate(request):
    """
    Manually generate or update monthly vehicle dues for any selected month/year
    based on active student bus passes.
    """
    today = date.today()
    month = int(request.POST.get('month', request.GET.get('month', today.month)))
    year = int(request.POST.get('year', request.GET.get('year', today.year)))

    setting = VehicleBillingSetting.objects.first()
    due_day = setting.due_day_of_month if setting else 1

    res = generate_monthly_vehicle_dues(year=year, month=month, due_day=due_day)
    month_name = calendar.month_name[month]
    messages.success(
        request,
        f"Monthly vehicle dues for {month_name} {year} updated: {res['created']} generated, {res['updated']} synchronized with current stop rates."
    )
    return redirect(f"/fees/vehicle/?month={month}&year={year}")


@login_required
def vehicle_billing_setting_update(request):
    """
    Configure vehicle billing settings (due day of month: 1st or user-determined date).
    """
    setting = VehicleBillingSetting.objects.first()
    if not setting:
        setting = VehicleBillingSetting.objects.create(due_day_of_month=1, auto_generate=True)

    if request.method == 'POST':
        form = VehicleBillingSettingForm(request.POST, instance=setting)
        if form.is_valid():
            setting = form.save()
            messages.success(
                request,
                f"Vehicle billing date updated! Dues are generated and due on the {setting.due_day_of_month}th of every month."
            )
            return redirect('fees:vehicle_fee_dashboard')
    else:
        form = VehicleBillingSettingForm(instance=setting)

    return render(request, 'fees/vehicle_setting_form.html', {'form': form, 'setting': setting})


@login_required
def download_vehicle_defaulters_pdf(request):
    """
    Downloads vehicle fee status & defaulters as a formatted PDF.
    """
    today = date.today()
    try:
        month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        month = today.month

    try:
        year = int(request.GET.get('year', today.year))
    except (ValueError, TypeError):
        year = today.year

    bus_stop_id = request.GET.get('bus_stop_id')
    bus_stop = BusStop.objects.filter(id=bus_stop_id).first() if bus_stop_id else None

    month_dues_qs = StudentMonthlyVehicleFee.objects.filter(
        month=month, year=year
    ).select_related('student__current_class', 'bus_stop')

    if bus_stop:
        month_dues_qs = month_dues_qs.filter(bus_stop=bus_stop)

    unpaid_dues = list(month_dues_qs.filter(is_paid=False).order_by('bus_stop__stop_name', 'student__full_name'))

    paid_payments = StudentFeePayment.objects.filter(
        fee_type=StudentFeePayment.FeeType.VEHICLE_MONTHLY,
        monthly_vehicle_fee__in=month_dues_qs.filter(is_paid=True)
    ).select_related('student__current_class', 'monthly_vehicle_fee__bus_stop')

    paid_records = []
    for p in paid_payments:
        paid_records.append({
            'receipt_number': p.receipt_number,
            'student_name': p.student.full_name,
            'bus_stop_name': p.monthly_vehicle_fee.bus_stop.stop_name if p.monthly_vehicle_fee and p.monthly_vehicle_fee.bus_stop else '—',
            'payment_date': p.payment_date,
            'payment_mode': p.get_payment_mode_display(),
            'amount_paid': p.amount_paid,
        })

    pdf_data = generate_vehicle_defaulters_pdf(month, year, paid_records, unpaid_dues, bus_stop)
    month_name = calendar.month_name[month]
    response = HttpResponse(pdf_data, content_type='application/pdf')
    stop_slug = f"_{bus_stop.stop_name.replace(' ', '_')}" if bus_stop else ""
    response['Content-Disposition'] = f'attachment; filename="Vehicle_Fee_Defaulters_{month_name}_{year}{stop_slug}.pdf"'
    return response



