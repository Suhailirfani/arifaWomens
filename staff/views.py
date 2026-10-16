from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import StaffProfile
from .forms import StaffProfileForm

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
            staff = form.save()
            messages.success(request, f"Staff member '{staff.full_name}' ({staff.staff_id}) added successfully!")
            return redirect('staff:staff_profile', staff_id=staff.id)
    else:
        form = StaffProfileForm()

    return render(request, 'staff/staff_form.html', {'form': form, 'title': 'Add New Staff Member'})


@login_required
def staff_edit(request, staff_id):
    staff = get_object_or_404(StaffProfile, pk=staff_id)
    if request.method == 'POST':
        form = StaffProfileForm(request.POST, request.FILES, instance=staff)
        if form.is_valid():
            form.save()
            messages.success(request, f"Staff details for '{staff.full_name}' updated successfully!")
            return redirect('staff:staff_profile', staff_id=staff.id)
    else:
        form = StaffProfileForm(instance=staff)

    return render(request, 'staff/staff_form.html', {'form': form, 'staff': staff, 'title': f'Edit Staff: {staff.full_name}'})


@login_required
def staff_delete(request, staff_id):
    staff = get_object_or_404(StaffProfile, pk=staff_id)
    if request.method == 'POST':
        name = staff.full_name
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
