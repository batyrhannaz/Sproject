from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles):
    """
    Decorator to restrict view access to specific user roles.
    allowed_roles: string or list/tuple of strings (e.g. ['student', 'parent'])
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            messages.error(
                request,
                f"Раздел доступен только для роли: {', '.join(allowed_roles)}. Ваша текущая роль: {request.user.role_title}."
            )
            return redirect('dashboard')

        return _wrapped_view
    return decorator

