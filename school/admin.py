from django.contrib import admin
from .models import (
    SchoolClass, Subject, TeacherAssignment, StudentProfile, TeacherProfile,
    BellSchedule, Timetable, Grade, QuarterGrade, Attendance, Homework,
    Announcement, Message, SchoolNews
)


@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'letter', 'academic_year', 'class_teacher', 'shift')
    list_filter = ('number', 'shift', 'academic_year')
    search_fields = ('number', 'letter', 'class_teacher__last_name')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'subject', 'school_class')
    list_filter = ('school_class', 'subject')
    search_fields = ('teacher__first_name', 'teacher__last_name', 'subject__name')


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'school_class', 'date_of_birth', 'address')
    list_filter = ('school_class',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username', 'address')


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'qualification', 'cabinet_number', 'experience_years')
    search_fields = ('user__first_name', 'user__last_name', 'cabinet_number')


@admin.register(BellSchedule)
class BellScheduleAdmin(admin.ModelAdmin):
    list_display = ('shift', 'lesson_number', 'start_time', 'end_time', 'break_duration')
    list_filter = ('shift',)


@admin.register(Timetable)
class TimetableAdmin(admin.ModelAdmin):
    list_display = ('school_class', 'day_of_week', 'lesson_number', 'subject', 'teacher', 'room')
    list_filter = ('school_class', 'day_of_week')
    search_fields = ('subject__name', 'teacher__last_name', 'room')


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'school_class', 'grade_value', 'date', 'comment', 'teacher')
    list_filter = ('school_class', 'subject', 'grade_value', 'date')
    search_fields = ('student__last_name', 'student__first_name', 'comment')


@admin.register(QuarterGrade)
class QuarterGradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'quarter', 'academic_year', 'grade_value', 'teacher')
    list_filter = ('quarter', 'academic_year', 'subject')
    search_fields = ('student__last_name', 'student__first_name')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'school_class', 'date', 'lesson_number', 'status', 'teacher')
    list_filter = ('status', 'school_class', 'date')
    search_fields = ('student__last_name', 'student__first_name')


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'school_class', 'subject', 'teacher', 'assigned_date', 'due_date')
    list_filter = ('school_class', 'subject', 'due_date')
    search_fields = ('title', 'description')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'target_role', 'target_class', 'is_important', 'created_at')
    list_filter = ('target_role', 'is_important', 'created_at')
    search_fields = ('title', 'content')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'recipient__username', 'subject', 'body')


@admin.register(SchoolNews)
class SchoolNewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_published', 'published_at')
    list_filter = ('is_published', 'published_at')
    search_fields = ('title', 'summary', 'content')
