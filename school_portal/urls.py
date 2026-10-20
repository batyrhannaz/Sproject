"""
URL configuration for school_portal project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts.views import dashboard_redirect, custom_login_view, custom_logout_view
from school import public_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public pages
    path('', public_views.home_view, name='home'),
    path('news/', public_views.news_list_view, name='news_list'),
    path('news/<int:news_id>/', public_views.news_detail_view, name='news_detail'),
    path('bells/', public_views.bells_view, name='bells'),
    path('contacts/', public_views.contacts_view, name='contacts'),

    # Auth & accounts
    path('dashboard/', dashboard_redirect, name='dashboard'),
    path('login/', custom_login_view, name='login'),
    path('logout/', custom_logout_view, name='logout'),
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # School & Academic
    path('school/', include('school.urls', namespace='school')),

    # Library
    path('library/', include('library.urls', namespace='library')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
