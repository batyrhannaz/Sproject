from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('settings/', views.settings_view, name='settings'),
    path('export-data/', views.export_user_data, name='export_data'),
    path('password-reset/', views.password_reset_request_view, name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
]

