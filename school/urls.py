from django.urls import path
from . import views

app_name = 'school'

urlpatterns = [
    # Cabinets
    path('student/', views.student_cabinet_view, name='student_cabinet'),
    path('parent/', views.parent_cabinet_view, name='parent_cabinet'),
    path('teacher/', views.teacher_cabinet_view, name='teacher_cabinet'),
    path('director/', views.director_cabinet_view, name='director_cabinet'),

    # Academic tools
    path('journal/', views.class_journal_view, name='class_journal'),
    path('quarter-grades/', views.quarter_grades_view, name='quarter_grades'),
    path('homework/', views.homework_manage_view, name='homework_manage'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('announcements/', views.announcements_view, name='announcements'),
    path('messages/', views.messages_view, name='messages'),
    path('import-users/', views.import_users_view, name='import_users'),
]

