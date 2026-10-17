from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q

from accounts.models import User
from .models import StaffProfile
from .forms import StaffProfileForm, StaffBulkUploadForm
from .excel_utils import generate_staff_excel_template, parse_staff_bulk_excel

@login_required
def staff_list(request):
    query = request.GET.get('q', '').strip()
    dept = request.GET.get('dept', '').strip()

    staff_members = StaffProfile.objects.prefetch_related('subjects_taught', 'managed_classes').all()

    if dept:
        staff_members = staff_members.filter(department__iexact=dept)

    if query:
        staff_members = staff_members.filter(
            Q(full_name__icontains=query) |
            Q(staff_id__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(designation__icontains=query)
        )

    departments = StaffProfile.objects.exclude(department='').values_list('department', flat=True).distinct()

    context = {
        'staff_members': staff_members,
        'departments': departments,
        'query': query,
        'selected_dept': dept,
        'total_count': staff_members.count()
    }
    return render(request, 'staff/staff_list.html', context)


@login_required
def staff_create(request):
    if request.method == 'POST':
        form = StaffProfileForm(request.POST, request.FILES)
        if form.is_valid():
            staff = form.save(commit=False)
            create_login = form.cleaned_data.get('create_login_account')
            custom_username = form.cleaned_data.get('username')
            custom_password = form.cleaned_data.get('password')
            login_role = form.cleaned_data.get('login_role') or 'teacher'

            if create_login:
                username = custom_username.strip() if custom_username else staff.staff_id.strip()
                raw_password = custom_password.strip() if custom_password else 'staff123'

                user = User.objects.filter(username=username).first()
                if not user:
                    name_parts = staff.full_name.strip().split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    user = User.objects.create_user(
                        username=username,
                        password=raw_password,
                        role=login_role,
                        first_name=first_name,
                        last_name=last_name,
                        email=staff.email or '',
                        phone_number=staff.phone or ''
                    )
                else:
                    user.role = login_role
                    if custom_password:
                        user.set_password(raw_password)
                    user.save()
                staff.user = user

            staff.save()
            form.save_m2m()
            messages.success(request, f"Staff member '{staff.full_name}' ({staff.staff_id}) added successfully!")
            return redirect('staff:staff_profile', staff_id=staff.id)
    else:
        form = StaffProfileForm(initial={'create_login_account': True, 'login_role': 'teacher'})

    return render(request, 'staff/staff_form.html', {'form': form, 'title': 'Add New Staff Member'})


@login_required
def staff_edit(request, staff_id):
    staff = get_object_or_404(StaffProfile, pk=staff_id)
    if request.method == 'POST':
        form = StaffProfileForm(request.POST, request.FILES, instance=staff)
        if form.is_valid():
            staff = form.save(commit=False)
            create_login = form.cleaned_data.get('create_login_account')
            custom_username = form.cleaned_data.get('username')
            custom_password = form.cleaned_data.get('password')
            login_role = form.cleaned_data.get('login_role') or 'teacher'

            if staff.user:
                if custom_username and custom_username.strip() != staff.user.username:
                    existing = User.objects.filter(username=custom_username.strip()).exclude(pk=staff.user.pk).first()
                    if not existing:
                        staff.user.username = custom_username.strip()
                if custom_password:
                    staff.user.set_password(custom_password.strip())
                staff.user.role = login_role
                staff.user.email = staff.email or staff.user.email
                staff.user.phone_number = staff.phone or staff.user.phone_number
                staff.user.save()
            elif create_login:
                username = custom_username.strip() if custom_username else staff.staff_id.strip()
                raw_password = custom_password.strip() if custom_password else 'staff123'
                user = User.objects.filter(username=username).first()
                if not user:
                    name_parts = staff.full_name.strip().split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    user = User.objects.create_user(
                        username=username,
                        password=raw_password,
                        role=login_role,
                        first_name=first_name,
                        last_name=last_name,
                        email=staff.email or '',
                        phone_number=staff.phone or ''
                    )
                else:
                    user.role = login_role
                    if custom_password:
                        user.set_password(raw_password)
                    user.save()
                staff.user = user

            staff.save()
            form.save_m2m()
            messages.success(request, f"Staff details for '{staff.full_name}' updated successfully!")
            return redirect('staff:staff_profile', staff_id=staff.id)
    else:
        initial = {}
        if staff.user:
            initial['username'] = staff.user.username
            initial['login_role'] = staff.user.role
            initial['create_login_account'] = True
        else:
            initial['create_login_account'] = False
            initial['login_role'] = 'teacher'
        form = StaffProfileForm(instance=staff, initial=initial)

    return render(request, 'staff/staff_form.html', {'form': form, 'staff': staff, 'title': f'Edit Staff: {staff.full_name}'})


@login_required
def staff_delete(request, staff_id):
    staff = get_object_or_404(StaffProfile, pk=staff_id)
    if request.method == 'POST':
        name = staff.full_name
        if staff.user:
            staff.user.delete()
        else:
            staff.delete()
        messages.success(request, f"Staff member '{name}' has been deleted.")
        return redirect('staff:staff_list')
    return render(request, 'staff/staff_confirm_delete.html', {'staff': staff})


@login_required
def staff_profile(request, staff_id):
    staff = get_object_or_404(
        StaffProfile.objects.prefetch_related('subjects_taught', 'managed_classes'),
        pk=staff_id
    )
    return render(request, 'staff/staff_profile.html', {'staff': staff})


@login_required
def staff_bulk_upload(request):
    """
    Bulk Excel upload: uploads .xlsx, parses rows, validates, and batch creates staff & login accounts.
    """
    if request.method == 'POST':
        form = StaffBulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['excel_file']
            try:
                created_count, updated_count, errors = parse_staff_bulk_excel(excel_file)
                if created_count > 0 or updated_count > 0:
                    messages.success(request, f"Bulk staff upload completed: {created_count} staff added, {updated_count} updated.")
                if errors:
                    for err in errors[:5]:
                        messages.warning(request, err)
                    if len(errors) > 5:
                        messages.warning(request, f"...and {len(errors) - 5} more row warnings.")
                return redirect('staff:staff_list')
            except Exception as e:
                messages.error(request, f"Error processing Excel file: {str(e)}")
    else:
        form = StaffBulkUploadForm()

    return render(request, 'staff/staff_bulk_upload.html', {'form': form})


@login_required
def download_staff_template(request):
    """
    Download empty or prefilled Excel template for bulk staff registration.
    """
    excel_content = generate_staff_excel_template()
    response = HttpResponse(
        excel_content,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="arifa_staff_bulk_upload_template.xlsx"'
    return response
