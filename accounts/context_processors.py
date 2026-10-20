from django.utils import timezone
from accounts.models import Role


def user_portal_context(request):
    context = {
        'all_roles': Role.choices,
        'user_role': None,
        'unread_messages_count': 0,
        'user_overdue_books_count': 0,
        'pending_reservations_count': 0,
        'user_active_loans_count': 0,
    }

    if request.user.is_authenticated:
        user = request.user
        context['user_role'] = user.role

        # Messages
        try:
            from school.models import Message
            context['unread_messages_count'] = Message.objects.filter(recipient=user, is_read=False).count()
        except Exception:
            pass

        # Overdue books notification for student & parent
        try:
            from library.models import BorrowRecord, Reservation
            today = timezone.now().date()

            if user.is_student:
                active_loans = BorrowRecord.objects.filter(reader=user, return_date__isnull=True)
                context['user_active_loans_count'] = active_loans.count()
                context['user_overdue_books_count'] = active_loans.filter(due_date__lt=today).count()
            elif user.is_parent:
                children_ids = user.children_relations.values_list('student_id', flat=True)
                active_loans = BorrowRecord.objects.filter(reader_id__in=children_ids, return_date__isnull=True)
                context['user_active_loans_count'] = active_loans.count()
                context['user_overdue_books_count'] = active_loans.filter(due_date__lt=today).count()
            elif user.is_librarian:
                context['pending_reservations_count'] = Reservation.objects.filter(status='pending').count()
                context['librarian_overdue_count'] = BorrowRecord.objects.filter(return_date__isnull=True, due_date__lt=today).count()
        except Exception:
            pass

    return context

