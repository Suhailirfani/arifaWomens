from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomLoginForm
from .models import User

def login_view(request):
    if request.user.is_authenticated:
        return redirect('redirect_dashboard')

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            return redirect('redirect_dashboard')
        else:
            messages.error(request, "Invalid username or password. Please check your credentials.")
    else:
        form = CustomLoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('home')

@login_required
def redirect_dashboard(request):
    """
    Intelligent role-based dashboard router.
    """
    user = request.user
    if user.is_superuser or user.role == User.Role.ADMIN:
        return redirect('dashboard:admin_dashboard')
    elif user.role == User.Role.OFFICE_STAFF:
        return redirect('dashboard:staff_dashboard')
    elif user.role == User.Role.TEACHER:
        return redirect('dashboard:teacher_dashboard')
    elif user.role == User.Role.PARENT:
        return redirect('dashboard:student_dashboard')
    else:
        return redirect('dashboard:admin_dashboard')
