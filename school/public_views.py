from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from school.models import SchoolNews, BellSchedule, Announcement, SchoolClass
from library.models import Book


def home_view(request):
    """
    Public landing page for the school.
    """
    news_list = SchoolNews.objects.filter(is_published=True).order_by('-published_at')[:3]
    announcements = Announcement.objects.filter(target_role='all').order_by('-is_important', '-created_at')[:4]
    bells_shift1 = BellSchedule.objects.filter(shift=1).order_by('lesson_number')[:5]
    new_books = Book.objects.filter(is_new=True)[:4] or Book.objects.all().order_by('-created_at')[:4]

    return render(request, 'public/home.html', {
        'news_list': news_list,
        'announcements': announcements,
        'bells_shift1': bells_shift1,
        'new_books': new_books,
    })


def news_list_view(request):
    news_list = SchoolNews.objects.filter(is_published=True).order_by('-published_at')
    return render(request, 'public/news_list.html', {'news_list': news_list})


def news_detail_view(request, news_id):
    news = get_object_or_404(SchoolNews, id=news_id, is_published=True)
    return render(request, 'public/news_detail.html', {'news': news})


def bells_view(request):
    shift1 = BellSchedule.objects.filter(shift=1).order_by('lesson_number')
    shift2 = BellSchedule.objects.filter(shift=2).order_by('lesson_number')
    return render(request, 'public/bells.html', {
        'shift1': shift1,
        'shift2': shift2,
    })


def contacts_view(request):
    if request.method == 'POST':
        messages.success(request, "Ваше обращение принято администрацией школы. Мы свяжемся с вами в ближайшее время.")
        return redirect('contacts')
    return render(request, 'public/contacts.html')

