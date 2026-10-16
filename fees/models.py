from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

class FeeCategory(models.Model):
    class FeeType(models.TextChoices):
        INSTALLMENT = 'installment', 'Installment-wise (Course Fee)'
        MONTHLY = 'monthly', 'Monthly Recurring (e.g. Vehicle Fee)'
        ONE_TIME = 'one_time', 'One-time Fee'

    name = models.CharField(max_length=100)
    fee_type = models.CharField(max_length=20, choices=FeeType.choices, default=FeeType.INSTALLMENT)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Fee Categories'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_fee_type_display()})"


class FeeStructure(models.Model):
    title = models.CharField(max_length=150, help_text="e.g. Plus One Humanities Course Fee")
    category = models.ForeignKey(FeeCategory, on_delete=models.CASCADE, related_name='structures')
    school_class = models.ForeignKey(
        'academics.SchoolClass',
        on_delete=models.CASCADE,
        related_name='fee_structures',
        null=True,
        blank=True,
        help_text="Optional class-specific assignment"
    )
    grade = models.ForeignKey(
        'academics.GradeLevel',
        on_delete=models.CASCADE,
        related_name='fee_structures',
        null=True,
        blank=True,
        help_text="Optional grade-wide assignment"
    )
    academic_year = models.ForeignKey(
        'academics.AcademicYear',
        on_delete=models.CASCADE,
        related_name='fee_structures'
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-academic_year', 'title']

    @property
    def installments_total(self):
        return self.installments.aggregate(tot=models.Sum('amount'))['tot'] or Decimal('0.00')

    @property
    def installments_count(self):
        return self.installments.count()

    def __str__(self):
        return f"{self.title} - ₹{self.total_amount} ({self.academic_year.name})"


class FeeInstallment(models.Model):
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='installments')
    title = models.CharField(max_length=150, help_text="e.g. 1st Installment (Admission), June Bus Fee")
    installment_number = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_current_due = models.BooleanField(
        default=False,
        help_text="Check if this is currently the active due installment for tracking defaulters"
    )
    requires_vehicle = models.BooleanField(
        default=False,
        help_text="If true, applies only to students with transportation/bus opted"
    )
    month = models.PositiveIntegerField(null=True, blank=True, help_text="1 to 12 for monthly fees")
    year = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['due_date', 'installment_number']

    def __str__(self):
        return f"{self.fee_structure.title} - {self.title} (₹{self.amount}, Due: {self.due_date})"

    def save(self, *args, **kwargs):
        if self.is_current_due:
            # Optionally mark other installments of same structure not current
            FeeInstallment.objects.filter(
                fee_structure=self.fee_structure,
                is_current_due=True
            ).exclude(pk=self.pk).update(is_current_due=False)
        super().save(*args, **kwargs)

    @property
    def total_collected(self):
        return self.payments.aggregate(total=models.Sum('amount_paid'))['total'] or Decimal('0.00')

    @property
    def payments_count(self):
        return self.payments.count()

    @property
    def due_status(self):
        today = timezone.localdate()
        if self.is_current_due:
            return 'active'
        if self.due_date < today:
            return 'overdue'
        return 'upcoming'

    @property
    def days_until_due(self):
        today = timezone.localdate()
        return (self.due_date - today).days


def auto_sync_due_installments():
    """
    Automatically rolls over and updates active due installments across all fee structures
    based on the current calendar date.
    
    Rule:
    - Finds the earliest installment in the structure whose due_date >= today (the current active/upcoming due target).
    - If all installment due dates are in the past, the latest installment is marked as active.
    - Sets is_current_due=True on the active target and False on others.
    """
    today = timezone.localdate()
    for structure in FeeStructure.objects.all():
        installments = list(structure.installments.order_by('due_date', 'installment_number'))
        if not installments:
            continue
        
        # Determine which installment should be active
        active_target = None
        for inst in installments:
            if inst.due_date >= today:
                active_target = inst
                break
        if not active_target:
            active_target = installments[-1]
            
        for inst in installments:
            should_be_current = (inst.id == active_target.id)
            if inst.is_current_due != should_be_current:
                FeeInstallment.objects.filter(id=inst.id).update(is_current_due=should_be_current)


class BusStop(models.Model):
    """
    Fixed monthly fee definition for academy transportation stops.
    Students boarding from this stop pay this monthly fee.
    """
    stop_name = models.CharField(max_length=120, unique=True, help_text="e.g. Pantheerankavu, Feroke Petta, Ramanattukara Junction")
    route_name = models.CharField(max_length=120, blank=True, help_text="e.g. Route 1 - Feroke, Route 2 - Ramanattukara")
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, help_text="Fixed monthly vehicle fee in ₹")
    pickup_time = models.CharField(max_length=30, blank=True, help_text="e.g. 07:45 AM")
    drop_time = models.CharField(max_length=30, blank=True, help_text="e.g. 04:30 PM")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['route_name', 'stop_name']

    def __str__(self):
        route_str = f" ({self.route_name})" if self.route_name else ""
        return f"{self.stop_name}{route_str} - ₹{self.monthly_fee}/month"

    @property
    def assigned_students_count(self):
        return self.student_passes.filter(is_active=True).count()


class StudentVehiclePass(models.Model):
    """
    Assigns a student to a BusStop with optional standing concession (partial usage discount).
    """
    class DiscountType(models.TextChoices):
        NONE = 'none', 'No Concession (Full Stop Fee)'
        FIXED = 'fixed', 'Reduce Exact Amount (₹)'
        PERCENTAGE = 'percent', 'Reduce Percentage (%)'

    student = models.OneToOneField(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='vehicle_pass'
    )
    bus_stop = models.ForeignKey(
        BusStop,
        on_delete=models.PROTECT,
        related_name='student_passes'
    )
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.NONE
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Exact amount in ₹ or percentage to reduce"
    )
    discount_reason = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g. One-way travel only, Sibling concession, Staff child"
    )
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(default=timezone.now)

    class Meta:
        verbose_name = 'Student Vehicle Pass'
        verbose_name_plural = 'Student Vehicle Passes'

    def __str__(self):
        return f"{self.student.full_name} - {self.bus_stop.stop_name} (Effective: ₹{self.calculated_monthly_fee}/mo)"

    @property
    def calculated_monthly_fee(self):
        base = self.bus_stop.monthly_fee
        if self.discount_type == self.DiscountType.FIXED:
            return max(Decimal('0.00'), base - self.discount_value)
        elif self.discount_type == self.DiscountType.PERCENTAGE:
            pct = min(Decimal('100.00'), max(Decimal('0.00'), self.discount_value))
            return max(Decimal('0.00'), base * (Decimal('1.00') - (pct / Decimal('100.00'))))
        return base


class VehicleBillingSetting(models.Model):
    """
    Settings governing monthly vehicle fee billing dates and automatic due generation.
    """
    due_day_of_month = models.PositiveIntegerField(
        default=1,
        help_text="Day of month when monthly vehicle fee is due (e.g. 1st, 5th, 10th of every month)"
    )
    auto_generate = models.BooleanField(
        default=True,
        help_text="Automatically update and generate monthly dues when billing day arrives"
    )
    academic_months = models.CharField(
        max_length=100,
        default='6,7,8,9,10,11,12,1,2,3',
        help_text="Comma-separated month numbers when academy operates (e.g. June to March)"
    )

    def __str__(self):
        return f"Vehicle Billing Settings (Due on day {self.due_day_of_month} of every month)"


class StudentMonthlyVehicleFee(models.Model):
    """
    Monthly vehicle fee due record for each student.
    Can be individually customized for partial month usage by reducing exact ₹ or %.
    """
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='monthly_vehicle_dues'
    )
    bus_stop = models.ForeignKey(
        BusStop,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='monthly_dues'
    )
    academic_year = models.ForeignKey(
        'academics.AcademicYear',
        on_delete=models.CASCADE,
        related_name='vehicle_dues'
    )
    month = models.PositiveIntegerField(help_text="1 to 12")
    year = models.PositiveIntegerField()
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base bus stop fee")
    
    # Month-specific customization (e.g. partial usage)
    custom_discount_type = models.CharField(
        max_length=20,
        choices=StudentVehiclePass.DiscountType.choices,
        default=StudentVehiclePass.DiscountType.NONE
    )
    custom_discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    custom_notes = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reason for partial usage concession"
    )
    
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'month', 'year')
        ordering = ['-year', '-month', 'student']

    def __str__(self):
        import calendar
        month_name = calendar.month_name[self.month]
        status = 'PAID' if self.is_paid else 'DUE'
        return f"{self.student.full_name} - {month_name} {self.year}: ₹{self.final_amount} ({status})"

    @property
    def month_name(self):
        import calendar
        return calendar.month_name[self.month]

    @property
    def is_overdue(self):
        return not self.is_paid and self.due_date < timezone.localdate()


def generate_monthly_vehicle_dues(year=None, month=None, due_day=None):
    """
    Generates or refreshes monthly vehicle dues for all students with an active VehiclePass.
    Due date is determined by due_day (or VehicleBillingSetting.due_day_of_month, default: 1st of month).
    """
    import calendar
    today = timezone.localdate()
    year = year or today.year
    month = month or today.month

    setting = VehicleBillingSetting.objects.first()
    if not due_day:
        due_day = setting.due_day_of_month if setting else 1

    max_days = calendar.monthrange(year, month)[1]
    safe_day = min(due_day, max_days)
    from datetime import date
    month_due_date = date(year, month, safe_day)

    from academics.models import AcademicYear
    current_ay = AcademicYear.objects.filter(is_current=True).first() or AcademicYear.objects.order_by('-start_date').first()

    active_passes = StudentVehiclePass.objects.filter(is_active=True, student__is_active=True).select_related('student', 'bus_stop')
    created_count = 0
    updated_count = 0

    for vpass in active_passes:
        calc_amount = vpass.calculated_monthly_fee

        fee_record, created = StudentMonthlyVehicleFee.objects.get_or_create(
            student=vpass.student,
            month=month,
            year=year,
            defaults={
                'bus_stop': vpass.bus_stop,
                'academic_year': current_ay or vpass.student.academic_year,
                'base_fee': vpass.bus_stop.monthly_fee,
                'custom_discount_type': vpass.discount_type,
                'custom_discount_value': vpass.discount_value,
                'custom_notes': vpass.discount_reason,
                'final_amount': calc_amount,
                'due_date': month_due_date,
            }
        )
        if created:
            created_count += 1
        elif not fee_record.is_paid and not fee_record.custom_notes:
            # Sync uncustomized unpaid record with pass updates
            fee_record.bus_stop = vpass.bus_stop
            fee_record.base_fee = vpass.bus_stop.monthly_fee
            fee_record.custom_discount_type = vpass.discount_type
            fee_record.custom_discount_value = vpass.discount_value
            fee_record.final_amount = calc_amount
            fee_record.due_date = month_due_date
            fee_record.save()
            updated_count += 1

    return {'created': created_count, 'updated': updated_count, 'month': month, 'year': year, 'due_date': month_due_date}


class StudentFeePayment(models.Model):
    class PaymentMode(models.TextChoices):
        CASH = 'CASH', 'Cash'
        UPI = 'UPI', 'UPI / GPay / PhonePe'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer (NEFT/IMPS)'
        CHEQUE = 'CHEQUE', 'Cheque'

    class FeeType(models.TextChoices):
        INSTALLMENT = 'installment', 'Course Fee Installment'
        VEHICLE_MONTHLY = 'monthly_vehicle', 'Monthly Vehicle Fee'
        OTHER = 'other', 'Other Fee'

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='fee_payments')
    fee_type = models.CharField(max_length=30, choices=FeeType.choices, default=FeeType.INSTALLMENT)
    installment = models.ForeignKey(FeeInstallment, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    monthly_vehicle_fee = models.ForeignKey(StudentMonthlyVehicleFee, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_mode = models.CharField(max_length=20, choices=PaymentMode.choices, default=PaymentMode.UPI)
    transaction_id = models.CharField(max_length=100, blank=True, help_text="UTR / Reference / Cheque number")
    receipt_number = models.CharField(max_length=50, unique=True)
    remarks = models.TextField(blank=True)
    collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collected_payments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"Receipt {self.receipt_number}: {self.student.full_name} - ₹{self.amount_paid}"

