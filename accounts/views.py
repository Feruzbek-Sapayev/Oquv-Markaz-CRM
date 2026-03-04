from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser
from .forms import CustomUserForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Xush kelibsiz, {user.get_full_name() or user.username}!')
            return redirect('dashboard:home')
        else:
            messages.error(request, 'Username yoki parol noto\'g\'ri!')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Tizimdan chiqildi.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html')


@login_required
def user_list(request):
    if not request.user.is_admin_role:
        messages.error(request, 'Ruxsatingiz yo\'q!')
        return redirect('dashboard:home')
    users = CustomUser.objects.all().order_by('role', 'username')
    return render(request, 'accounts/user_list.html', {'users': users})




@login_required
def user_create(request):
    if not request.user.is_superadmin:
        messages.error(request, 'Ruxsatingiz yo\'q!')
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = CustomUserForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            # Handle profile linking
            role = form.cleaned_data.get('role')
            if role == 'teacher':
                profile = form.cleaned_data.get('teacher_profile')
                if profile:
                    profile.user = user
                    profile.save()
            elif role == 'student':
                profile = form.cleaned_data.get('student_profile')
                if profile:
                    profile.user = user
                    profile.save()
            messages.success(request, 'Foydalanuvchi muvaffaqiyatli qo\'shildi!')
            return redirect('accounts:user_list')
    else:
        form = CustomUserForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Yangi foydalanuvchi'})


@login_required
def user_edit(request, pk):
    if not request.user.is_superadmin:
        messages.error(request, 'Ruxsatingiz yo\'q!')
        return redirect('dashboard:home')
    user = CustomUser.objects.get(pk=pk)
    if request.method == 'POST':
        form = CustomUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            user = form.save()
            # Handle profile linking
            role = form.cleaned_data.get('role')
            if role == 'teacher':
                profile = form.cleaned_data.get('teacher_profile')
                # Unlink old
                Teacher.objects.filter(user=user).update(user=None)
                if profile:
                    profile.user = user
                    profile.save()
            elif role == 'student':
                profile = form.cleaned_data.get('student_profile')
                # Unlink old
                Student.objects.filter(user=user).update(user=None)
                if profile:
                    profile.user = user
                    profile.save()
            messages.success(request, 'Foydalanuvchi tahrirlandi!')
            return redirect('accounts:user_list')
    else:
        form = CustomUserForm(instance=user)
    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Tahrirlash', 'obj': user})


@login_required
def user_delete(request, pk):
    if not request.user.is_superadmin:
        messages.error(request, 'Ruxsatingiz yo\'q!')
        return redirect('dashboard:home')
    user = CustomUser.objects.get(pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'Foydalanuvchi o\'chirildi!')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'obj': user})
