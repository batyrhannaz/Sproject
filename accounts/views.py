import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from .models import User, Role
from .forms import CustomLoginForm, UserSettingsForm, PasswordResetRequestForm


def dashboard_redirect(request):
    if not request.user.is_authenticated:
        return redirect('public:home')

    role = request.user.role
    if role == Role.STUDENT:
        return redirect('school:student_cabinet')
    elif role == Role.PARENT:
        return redirect('school:parent_cabinet')
    elif role == Role.TEACHER:
        return redirect('school:teacher_cabinet')
    elif role == Role.LIBRARIAN:
        return redirect('library:librarian_cabinet')
    elif role == Role.DIRECTOR or request.user.is_superuser:
        return redirect('school:director_cabinet')

    return redirect('school:student_cabinet')


def custom_login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    selected_role = request.GET.get('role', Role.STUDENT)
    
    # Handle quick demo switch from button
    demo_login = request.GET.get('demo')
    if demo_login:
        user = authenticate(request, username=demo_login, password='password123')
        if user is not None:
            login(request, user)
            messages.success(request, f"Добро пожаловать, {user.display_name}! Вы вошли в роли «{user.role_title}».")
            return redirect('dashboard')

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        role = request.POST.get('role', selected_role)
        if form.is_valid():
            user = form.get_user()
            # If role is explicitly chosen, verify user's role or allow director/superuser
            if role and user.role != role and not user.is_superuser:
                messages.warning(
                    request,
                    f"Ваш аккаунт зарегистрирован как «{user.role_title}», вход выполнен в соответствующий кабинет."
                )
            login(request, user)
            messages.success(request, f"С возвращением, {user.display_name}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
        else:
            messages.error(request, "Неверный логин или пароль. Попробуйте снова.")
    else:
        form = CustomLoginForm()

    return render(request, 'accounts/login.html', {
        'form': form,
        'selected_role': selected_role,
        'roles': Role.choices,
    })


def custom_logout_view(request):
    if request.user.is_authenticated:
        username = request.user.display_name
        logout(request)
        messages.info(request, f"Вы успешно вышли из системы. До свидания, {username}!")
    return redirect('login')


@login_required
def settings_view(request):
    user = request.user
    user_form = UserSettingsForm(instance=user)
    password_form = PasswordChangeForm(user=user)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'update_profile':
            user_form = UserSettingsForm(request.POST, request.FILES, instance=user)
            if user_form.is_valid():
                user_form.save()
                messages.success(request, "Настройки профиля успешно сохранены!")
                return redirect('accounts:settings')
            else:
                messages.error(request, "Пожалуйста, проверьте введённые данные.")

        elif action == 'change_password':
            password_form = PasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                saved_user = password_form.save()
                update_session_auth_hash(request, saved_user)
                messages.success(request, "Пароль был успешно изменён!")
                return redirect('accounts:settings')
            else:
                messages.error(request, "Ошибка при смене пароля. Убедитесь, что старый пароль верный.")

    return render(request, 'accounts/settings.html', {
        'user_form': user_form,
        'password_form': password_form,
    })


@login_required
def export_user_data(request):
    """
    Exports user profile data, attendance, grades, and library borrowings as JSON.
    """
    user = request.user
    data = {
        'username': user.username,
        'full_name': user.get_full_name(),
        'role': user.role_title,
        'email': user.email,
        'linked_gmail': user.linked_gmail,
        'phone': user.phone,
        'preferred_language': user.preferred_language,
        'font_size': user.font_size,
    }

    if user.is_student:
        if hasattr(user, 'student_profile') and user.student_profile.school_class:
            data['school_class'] = user.student_profile.school_class.name
        
        grades_list = []
        for g in user.grades.select_related('subject').all():
            grades_list.append({
                'subject': g.subject.name,
                'date': g.date.isoformat(),
                'grade': g.grade_value,
                'comment': g.comment,
            })
        data['grades'] = grades_list

        borrows_list = []
        for b in user.borrow_records.select_related('copy__book').all():
            borrows_list.append({
                'book': b.copy.book.title,
                'author': b.copy.book.author,
                'borrow_date': b.borrow_date.isoformat(),
                'due_date': b.due_date.isoformat(),
                'return_date': b.return_date.isoformat() if b.return_date else None,
                'is_overdue': b.is_overdue,
            })
        data['library_borrowings'] = borrows_list

    response = HttpResponse(
        json.dumps(data, indent=2, ensure_ascii=False),
        content_type='application/json; charset=utf-8'
    )
    response['Content-Disposition'] = f'attachment; filename="user_data_{user.username}.json"'
    return response


def password_reset_request_view(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['identifier'].strip()
            user = User.objects.filter(username__iexact=identifier).first() or \
                   User.objects.filter(linked_gmail__iexact=identifier).first() or \
                   User.objects.filter(email__iexact=identifier).first()

            if user and (user.linked_gmail or user.email):
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_url = request.build_absolute_uri(f"/accounts/password-reset-confirm/{uid}/{token}/")
                target_email = user.linked_gmail or user.email
                
                subject = "Сброс пароля на школьном портале"
                body = (
                    f"Здравствуйте, {user.display_name}!\n\n"
                    f"Вы запросили сброс пароля для вашей учётной записи на школьном портале.\n"
                    f"Для установки нового пароля перейдите по следующей ссылке:\n"
                    f"{reset_url}\n\n"
                    f"Если вы не запрашивали сброс, просто проигнорируйте это письмо."
                )

                try:
                    send_mail(
                        subject,
                        body,
                        settings.DEFAULT_FROM_EMAIL,
                        [target_email],
                        fail_silently=False,
                    )
                    messages.success(
                        request,
                        f"Инструкция по сбросу пароля отправлена на почту {target_email}. "
                        f"(В режиме разработки ссылка выводится в консоль/терминал сервера)"
                    )
                except Exception as e:
                    # In development or if SMTP is not active, render fallback link
                    messages.info(
                        request,
                        f"Ссылка для восстановления сгенерирована (SMTP локально): {reset_url}"
                    )
                return render(request, 'accounts/password_reset_done.html', {'reset_url': reset_url})
            else:
                messages.error(request, "Пользователь с таким логином или привязанным Gmail не найден.")
    else:
        form = PasswordResetRequestForm()

    return render(request, 'accounts/password_reset_request.html', {'form': form})


def password_reset_confirm_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Ваш пароль успешно изменён! Теперь вы можете войти.")
                return redirect('login')
        else:
            form = SetPasswordForm(user)
        return render(request, 'accounts/password_reset_confirm.html', {'form': form, 'validlink': True})
    else:
        return render(request, 'accounts/password_reset_confirm.html', {'validlink': False})
