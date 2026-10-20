from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Avg, Count, Q
from django.http import HttpResponse
from datetime import timedelta, date
import csv
import io

from accounts.models import User, Role, ParentStudentRelation
from accounts.decorators import role_required
from school.models import (
    SchoolClass, Subject, TeacherAssignment, StudentProfile, TeacherProfile,
    BellSchedule, Timetable, Grade, QuarterGrade, Attendance, Homework,
    Announcement, Message, SchoolNews
)
from library.models import Book, BorrowRecord, Reservation


# ----------------------------------------------------
# 1. STUDENT CABINET
# ----------------------------------------------------
@login_required
@role_required(['student'])
def student_cabinet_view(request):
    user = request.user
    student_profile = getattr(user, 'student_profile', None)
    school_class = student_profile.school_class if student_profile else None

    # Timetable for this class
    timetable_by_day = {}
    if school_class:
        for day_num, day_name in Timetable.DAYS:
            items = Timetable.objects.filter(
                school_class=school_class, day_of_week=day_num
            ).select_related('subject', 'teacher').order_by('lesson_number')
            if items.exists():
                timetable_by_day[day_name] = items

    # Today's timetable
    today_weekday = timezone.now().isoweekday()  # 1 = Monday, 7 = Sunday
    today_lessons = []
    if school_class and today_weekday <= 6:
        today_lessons = Timetable.objects.filter(
            school_class=school_class, day_of_week=today_weekday
        ).select_related('subject', 'teacher').order_by('lesson_number')

    # Recent grades & average per subject
    recent_grades = Grade.objects.filter(student=user).select_related('subject', 'teacher').order_by('-date')[:15]
    
    subject_averages = (
        Grade.objects.filter(student=user)
        .values('subject__name')
        .annotate(avg_grade=Avg('grade_value'), total_grades=Count('id'))
        .order_by('subject__name')
    )

    # Quarter grades
    quarter_grades = QuarterGrade.objects.filter(student=user).select_related('subject').order_by('quarter', 'subject__name')

    # Homeworks for this class
    homeworks = []
    if school_class:
        homeworks = Homework.objects.filter(
            school_class=school_class,
            due_date__gte=timezone.now().date() - timedelta(days=7)
        ).select_related('subject', 'teacher').order_by('due_date')

    # Attendance stats
    attendances = Attendance.objects.filter(student=user)
    total_attendance_records = attendances.count()
    absent_count = attendances.filter(status='absent').count()
    sick_count = attendances.filter(status='sick').count()
    valid_count = attendances.filter(status='valid').count()

    # Announcements
    announcements = Announcement.objects.filter(
        Q(target_role__in=['all', 'students']) | Q(target_class=school_class)
    ).distinct().order_by('-is_important', '-created_at')[:5]

    # Library borrowings
    active_borrows = BorrowRecord.objects.filter(
        reader=user, return_date__isnull=True
    ).select_related('copy__book').order_by('due_date')

    active_reservations = Reservation.objects.filter(
        reader=user, status__in=['pending', 'confirmed']
    ).select_related('book')

    return render(request, 'school/student_cabinet.html', {
        'student_profile': student_profile,
        'school_class': school_class,
        'today_lessons': today_lessons,
        'timetable_by_day': timetable_by_day,
        'recent_grades': recent_grades,
        'subject_averages': subject_averages,
        'quarter_grades': quarter_grades,
        'homeworks': homeworks,
        'total_attendance_records': total_attendance_records,
        'absent_count': absent_count,
        'sick_count': sick_count,
        'valid_count': valid_count,
        'announcements': announcements,
        'active_borrows': active_borrows,
        'active_reservations': active_reservations,
    })


# ----------------------------------------------------
# 2. PARENT CABINET
# ----------------------------------------------------
@login_required
@role_required(['parent'])
def parent_cabinet_view(request):
    user = request.user
    children_relations = user.children_relations.select_related('student__student_profile__school_class').all()

    if not children_relations.exists():
        messages.info(request, "К вашему аккаунту пока не привязаны ученики. Обратитесь к классному руководителю или директору.")
        return render(request, 'school/parent_cabinet.html', {'children': []})

    # Select child by query parameter or default to first
    selected_child_id = request.GET.get('child_id')
    selected_child = None
    if selected_child_id:
        selected_child = User.objects.filter(id=selected_child_id, parent_relations__parent=user).first()
    if not selected_child:
        selected_child = children_relations.first().student

    child_profile = getattr(selected_child, 'student_profile', None)
    child_class = child_profile.school_class if child_profile else None

    # Child's grades
    recent_grades = Grade.objects.filter(student=selected_child).select_related('subject', 'teacher').order_by('-date')[:20]
    subject_averages = (
        Grade.objects.filter(student=selected_child)
        .values('subject__name')
        .annotate(avg_grade=Avg('grade_value'), total_grades=Count('id'))
        .order_by('subject__name')
    )
    quarter_grades = QuarterGrade.objects.filter(student=selected_child).select_related('subject').order_by('quarter', 'subject__name')

    # Child's attendance
    attendances_qs = Attendance.objects.filter(student=selected_child)
    absent_count = attendances_qs.filter(status='absent').count()
    sick_count = attendances_qs.filter(status='sick').count()
    valid_count = attendances_qs.filter(status='valid').count()
    attendances = attendances_qs.order_by('-date')[:20]

    # Child's homework
    homeworks = []
    if child_class:
        homeworks = Homework.objects.filter(
            school_class=child_class,
            due_date__gte=timezone.now().date() - timedelta(days=5)
        ).select_related('subject', 'teacher').order_by('due_date')

    # Child's library borrowings
    child_borrows = BorrowRecord.objects.filter(
        reader=selected_child, return_date__isnull=True
    ).select_related('copy__book').order_by('due_date')

    # Announcements for parents
    announcements = Announcement.objects.filter(
        Q(target_role__in=['all', 'parents']) | Q(target_class=child_class)
    ).distinct().order_by('-is_important', '-created_at')[:5]

    return render(request, 'school/parent_cabinet.html', {
        'children_relations': children_relations,
        'selected_child': selected_child,
        'child_profile': child_profile,
        'child_class': child_class,
        'recent_grades': recent_grades,
        'subject_averages': subject_averages,
        'quarter_grades': quarter_grades,
        'attendances': attendances,
        'absent_count': absent_count,
        'sick_count': sick_count,
        'valid_count': valid_count,
        'homeworks': homeworks,
        'child_borrows': child_borrows,
        'announcements': announcements,
    })


# ----------------------------------------------------
# 3. TEACHER CABINET & JOURNAL
# ----------------------------------------------------
@login_required
@role_required(['teacher'])
def teacher_cabinet_view(request):
    user = request.user
    teacher_profile = getattr(user, 'teacher_profile', None)
    supervised_classes = user.supervised_classes.all()
    assignments = user.assignments.select_related('subject', 'school_class').all()

    # Teacher's today schedule
    today_weekday = timezone.now().isoweekday()
    today_lessons = Timetable.objects.filter(
        teacher=user, day_of_week=today_weekday
    ).select_related('subject', 'school_class').order_by('lesson_number')

    # Recent given grades
    recent_grades = Grade.objects.filter(teacher=user).select_related('student', 'subject', 'school_class').order_by('-created_at')[:10]

    # Active homeworks assigned by this teacher
    active_homeworks = Homework.objects.filter(teacher=user, due_date__gte=timezone.now().date()).order_by('due_date')

    # Announcements
    announcements = Announcement.objects.filter(
        Q(target_role__in=['all', 'teachers'])
    ).order_by('-is_important', '-created_at')[:5]

    return render(request, 'school/teacher_cabinet.html', {
        'teacher_profile': teacher_profile,
        'supervised_classes': supervised_classes,
        'assignments': assignments,
        'today_lessons': today_lessons,
        'recent_grades': recent_grades,
        'active_homeworks': active_homeworks,
        'announcements': announcements,
    })


@login_required
@role_required(['teacher', 'director'])
def class_journal_view(request):
    """
    Electronic Class Journal: select class, subject, date.
    View student roster and submit grades / attendance.
    """
    user = request.user
    assignments = user.assignments.select_related('subject', 'school_class').all() if user.is_teacher else TeacherAssignment.objects.all()

    # If teacher has assignments, default to first; else all classes/subjects
    class_id = request.GET.get('class_id')
    subject_id = request.GET.get('subject_id')
    selected_date_str = request.GET.get('date', timezone.now().date().isoformat())

    try:
        journal_date = date.fromisoformat(selected_date_str)
    except (ValueError, TypeError):
        journal_date = timezone.now().date()

    classes = SchoolClass.objects.all().order_by('number', 'letter')
    subjects = Subject.objects.all().order_by('name')

    selected_class = None
    if class_id:
        selected_class = SchoolClass.objects.filter(id=class_id).first()
    elif assignments.exists():
        selected_class = assignments.first().school_class
    elif classes.exists():
        selected_class = classes.first()

    selected_subject = None
    if subject_id:
        selected_subject = Subject.objects.filter(id=subject_id).first()
    elif assignments.filter(school_class=selected_class).exists():
        selected_subject = assignments.filter(school_class=selected_class).first().subject
    elif subjects.exists():
        selected_subject = subjects.first()

    students = []
    if selected_class:
        students = User.objects.filter(
            student_profile__school_class=selected_class, role=Role.STUDENT
        ).select_related('student_profile').order_by('last_name', 'first_name')

    # Handle POST submission for grading & attendance
    if request.method == 'POST' and selected_class and selected_subject:
        saved_grades = 0
        saved_attendance = 0

        for student in students:
            # Grade
            grade_key = f"grade_{student.id}"
            comment_key = f"comment_{student.id}"
            grade_val = request.POST.get(grade_key)
            comment_val = request.POST.get(comment_key, '').strip()

            if grade_val and grade_val.isdigit():
                Grade.objects.update_or_create(
                    student=student,
                    subject=selected_subject,
                    school_class=selected_class,
                    date=journal_date,
                    defaults={
                        'grade_value': int(grade_val),
                        'comment': comment_val,
                        'teacher': user if user.is_teacher else None,
                    }
                )
                saved_grades += 1
            elif grade_val == '':
                # If cleared, delete existing grade on that date if any
                Grade.objects.filter(
                    student=student, subject=selected_subject,
                    school_class=selected_class, date=journal_date
                ).delete()

            # Attendance
            att_key = f"attendance_{student.id}"
            att_val = request.POST.get(att_key)
            if att_val in ['present', 'absent', 'sick', 'valid']:
                Attendance.objects.update_or_create(
                    student=student,
                    school_class=selected_class,
                    date=journal_date,
                    defaults={
                        'status': att_val,
                        'subject': selected_subject,
                        'teacher': user if user.is_teacher else None,
                    }
                )
                saved_attendance += 1

        messages.success(request, f"Журнал успешно сохранён за {journal_date.strftime('%d.%m.%Y')}! (Оценок: {saved_grades}, Отметок посещаемости: {saved_attendance})")
        return redirect(f"{request.path}?class_id={selected_class.id}&subject_id={selected_subject.id}&date={journal_date.isoformat()}")

    # Retrieve existing grades and attendance for this class, subject, and date
    existing_grades = {}
    existing_attendance = {}
    if selected_class and selected_subject:
        for g in Grade.objects.filter(school_class=selected_class, subject=selected_subject, date=journal_date):
            existing_grades[g.student_id] = g
        for a in Attendance.objects.filter(school_class=selected_class, date=journal_date):
            existing_attendance[a.student_id] = a.status

    # Historical dates for column matrix (last 10 lesson dates with grades)
    history_dates = []
    matrix_data = []
    if selected_class and selected_subject:
        dates_qs = Grade.objects.filter(
            school_class=selected_class, subject=selected_subject
        ).values_list('date', flat=True).distinct().order_by('-date')[:8]
        history_dates = sorted(list(dates_qs))

        for student in students:
            row = {'student': student, 'history_grades': []}
            for d in history_dates:
                gr = Grade.objects.filter(student=student, subject=selected_subject, date=d).first()
                row['history_grades'].append(gr.grade_value if gr else '—')
            # Current date data
            row['current_grade'] = existing_grades.get(student.id)
            row['current_attendance'] = existing_attendance.get(student.id, 'present')
            matrix_data.append(row)

    return render(request, 'school/class_journal.html', {
        'classes': classes,
        'subjects': subjects,
        'assignments': assignments,
        'selected_class': selected_class,
        'selected_subject': selected_subject,
        'journal_date': journal_date,
        'students': students,
        'matrix_data': matrix_data,
        'history_dates': history_dates,
    })


@login_required
@role_required(['teacher', 'director'])
def quarter_grades_view(request):
    """
    Quarter grades (четвертные оценки) entry and report card sheet.
    """
    classes = SchoolClass.objects.all().order_by('number', 'letter')
    subjects = Subject.objects.all().order_by('name')

    class_id = request.GET.get('class_id')
    subject_id = request.GET.get('subject_id')
    quarter = int(request.GET.get('quarter', 1))

    selected_class = SchoolClass.objects.filter(id=class_id).first() if class_id else classes.first()
    selected_subject = Subject.objects.filter(id=subject_id).first() if subject_id else subjects.first()

    students = []
    student_rows = []
    if selected_class and selected_subject:
        students = User.objects.filter(
            student_profile__school_class=selected_class, role=Role.STUDENT
        ).order_by('last_name', 'first_name')

        if request.method == 'POST':
            saved = 0
            for s in students:
                qval = request.POST.get(f"quarter_grade_{s.id}")
                if qval and qval.isdigit():
                    QuarterGrade.objects.update_or_create(
                        student=s, subject=selected_subject, quarter=quarter, academic_year='2026-2027',
                        defaults={'grade_value': int(qval), 'teacher': request.user if request.user.is_teacher else None}
                    )
                    saved += 1
            messages.success(request, f"Четвертные оценки сохранены ({saved} записей).")
            return redirect(f"{request.path}?class_id={selected_class.id}&subject_id={selected_subject.id}&quarter={quarter}")

        for s in students:
            q_grade = QuarterGrade.objects.filter(
                student=s, subject=selected_subject, quarter=quarter, academic_year='2026-2027'
            ).first()
            avg = Grade.objects.filter(student=s, subject=selected_subject).aggregate(avg=Avg('grade_value'))['avg']
            student_rows.append({
                'student': s,
                'average': round(avg, 2) if avg else '—',
                'quarter_grade': q_grade.grade_value if q_grade else '',
            })

    return render(request, 'school/quarter_grades.html', {
        'classes': classes,
        'subjects': subjects,
        'selected_class': selected_class,
        'selected_subject': selected_subject,
        'quarter': quarter,
        'student_rows': student_rows,
        'quarter_choices': QuarterGrade.QUARTERS,
    })


@login_required
@role_required(['teacher', 'director'])
def homework_manage_view(request):
    """
    Teacher creates and manages homework assignments.
    """
    user = request.user
    if request.method == 'POST':
        class_id = request.POST.get('school_class')
        subject_id = request.POST.get('subject')
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date_str = request.POST.get('due_date')
        attachment = request.FILES.get('attachment')

        if class_id and subject_id and title and due_date_str:
            school_class = get_object_or_404(SchoolClass, id=class_id)
            subject = get_object_or_404(Subject, id=subject_id)
            Homework.objects.create(
                school_class=school_class,
                subject=subject,
                teacher=user,
                title=title,
                description=description,
                due_date=date.fromisoformat(due_date_str),
                attachment=attachment
            )
            messages.success(request, f"Домашнее задание для {school_class.name} успешно опубликовано!")
            return redirect('school:homework_manage')
        else:
            messages.error(request, "Заполните все обязательные поля формы.")

    homeworks = Homework.objects.filter(teacher=user).select_related('school_class', 'subject').order_by('-due_date')
    classes = SchoolClass.objects.all().order_by('number', 'letter')
    subjects = Subject.objects.all().order_by('name')

    return render(request, 'school/homework_manage.html', {
        'homeworks': homeworks,
        'classes': classes,
        'subjects': subjects,
    })


# ----------------------------------------------------
# 4. DIRECTOR CABINET & IMPORT
# ----------------------------------------------------
@login_required
@role_required(['director'])
def director_cabinet_view(request):
    """
    Director cabinet: school stats, user management, announcements, import.
    """
    total_students = User.objects.filter(role=Role.STUDENT).count()
    total_teachers = User.objects.filter(role=Role.TEACHER).count()
    total_parents = User.objects.filter(role=Role.PARENT).count()
    total_classes = SchoolClass.objects.count()

    # Library stats for director
    total_books = Book.objects.count()
    active_borrows_count = BorrowRecord.objects.filter(return_date__isnull=True).count()
    overdue_count = BorrowRecord.objects.filter(return_date__isnull=True, due_date__lt=timezone.now().date()).count()

    # School performance average
    avg_performance = Grade.objects.aggregate(avg=Avg('grade_value'))['avg']
    avg_performance = round(avg_performance, 2) if avg_performance else 0.0

    # User search / filter
    role_filter = request.GET.get('role_filter', '')
    query = request.GET.get('q', '').strip()

    users_qs = User.objects.all().select_related('student_profile__school_class', 'teacher_profile').order_by('role', 'last_name')
    if role_filter:
        users_qs = users_qs.filter(role=role_filter)
    if query:
        users_qs = users_qs.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query)
        )
    users_list = users_qs[:40]

    # Quick create user modal handling
    if request.method == 'POST' and request.POST.get('action') == 'create_user':
        uname = request.POST.get('username')
        pwd = request.POST.get('password') or 'password123'
        role = request.POST.get('role')
        fname = request.POST.get('first_name')
        lname = request.POST.get('last_name')
        email = request.POST.get('email')
        class_id = request.POST.get('school_class')

        if uname and role:
            if User.objects.filter(username=uname).exists():
                messages.error(request, f"Пользователь с логином «{uname}» уже существует!")
            else:
                new_user = User.objects.create_user(
                    username=uname, password=pwd, role=role,
                    first_name=fname, last_name=lname, email=email
                )
                if role == Role.STUDENT and class_id:
                    s_class = SchoolClass.objects.filter(id=class_id).first()
                    StudentProfile.objects.create(user=new_user, school_class=s_class)
                elif role == Role.TEACHER:
                    TeacherProfile.objects.create(user=new_user)
                messages.success(request, f"Пользователь {new_user.display_name} ({new_user.role_title}) успешно создан!")
                return redirect('school:director_cabinet')

    classes = SchoolClass.objects.all().order_by('number', 'letter')

    return render(request, 'school/director_cabinet.html', {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_parents': total_parents,
        'total_classes': total_classes,
        'total_books': total_books,
        'active_borrows_count': active_borrows_count,
        'overdue_count': overdue_count,
        'avg_performance': avg_performance,
        'users_list': users_list,
        'role_filter': role_filter,
        'query': query,
        'classes': classes,
        'roles': Role.choices,
    })


@login_required
@role_required(['director'])
def import_users_view(request):
    """
    Import students and teachers from CSV or Excel file.
    Expected columns: role (student/teacher), username, password, first_name, last_name, class_name (e.g. 9-A), email
    """
    if request.method == 'POST' and request.FILES.get('data_file'):
        file = request.FILES['data_file']
        filename = file.name.lower()
        imported_count = 0
        errors = []

        try:
            rows = []
            if filename.endswith('.csv'):
                decoded_file = file.read().decode('utf-8-sig', errors='ignore')
                csv_reader = csv.reader(io.StringIO(decoded_file), delimiter=',' if ',' in decoded_file[:100] else ';')
                headers = [h.strip().lower() for h in next(csv_reader)]
                for line in csv_reader:
                    if line and any(line):
                        rows.append(dict(zip(headers, [val.strip() for val in line])))
            elif filename.endswith('.xlsx'):
                import openpyxl
                wb = openpyxl.load_workbook(file, data_only=True)
                sheet = wb.active
                iter_rows = sheet.iter_rows(values_only=True)
                header_row = next(iter_rows)
                headers = [str(h).strip().lower() if h else '' for h in header_row]
                for r in iter_rows:
                    if any(r):
                        row_dict = {headers[i]: str(r[i]).strip() if r[i] is not None else '' for i in range(len(headers))}
                        rows.append(row_dict)
            else:
                messages.error(request, "Поддерживаются только форматы CSV и Excel (.xlsx)!")
                return redirect('school:import_users')

            for idx, row in enumerate(rows, start=2):
                username = row.get('username') or row.get('логин')
                if not username:
                    continue
                role_str = (row.get('role') or row.get('роль') or 'student').lower()
                role = Role.STUDENT if 'учен' in role_str or 'stud' in role_str else Role.TEACHER
                pwd = row.get('password') or row.get('пароль') or 'password123'
                fname = row.get('first_name') or row.get('имя') or ''
                lname = row.get('last_name') or row.get('фамилия') or ''
                email = row.get('email') or row.get('почта') or f"{username}@school.edu"
                class_str = row.get('class_name') or row.get('класс') or ''

                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'role': role,
                        'first_name': fname,
                        'last_name': lname,
                        'email': email,
                    }
                )
                user.set_password(pwd)
                user.role = role
                user.first_name = fname
                user.last_name = lname
                user.save()

                if role == Role.STUDENT:
                    s_class = None
                    if class_str:
                        # parse "9-А" or "9А"
                        class_clean = class_str.replace(' ', '').replace('-', '')
                        num_part = ''.join([c for c in class_clean if c.isdigit()])
                        let_part = ''.join([c for c in class_clean if not c.isdigit()]).upper()
                        if num_part:
                            s_class, _ = SchoolClass.objects.get_or_create(
                                number=int(num_part), letter=let_part or 'А'
                            )
                    StudentProfile.objects.update_or_create(user=user, defaults={'school_class': s_class})
                elif role == Role.TEACHER:
                    TeacherProfile.objects.get_or_create(user=user)

                imported_count += 1

            messages.success(request, f"Успешно импортировано пользователей: {imported_count}!")
            return redirect('school:director_cabinet')

        except Exception as e:
            messages.error(request, f"Ошибка при разборе файла: {str(e)}")

    return render(request, 'school/import_users.html')


# ----------------------------------------------------
# 5. MESSAGES & ANNOUNCEMENTS & TIMETABLE
# ----------------------------------------------------
@login_required
def messages_view(request):
    """
    Internal messaging system between users (teachers, parents, students, librarians, director).
    """
    user = request.user
    
    # Handle new message submission
    if request.method == 'POST':
        recipient_id = request.POST.get('recipient_id')
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()

        if recipient_id and body:
            recipient = get_object_or_404(User, id=recipient_id)
            Message.objects.create(
                sender=user,
                recipient=recipient,
                subject=subject or "Без темы",
                body=body
            )
            messages.success(request, f"Сообщение успешно отправлено пользователю {recipient.display_name}!")
            return redirect('school:messages')
        else:
            messages.error(request, "Выберите получателя и введите текст сообщения.")

    # Mark as read if clicked
    read_id = request.GET.get('read_id')
    if read_id:
        Message.objects.filter(id=read_id, recipient=user).update(is_read=True)

    inbox = Message.objects.filter(recipient=user).select_related('sender').order_by('-created_at')
    outbox = Message.objects.filter(sender=user).select_related('recipient').order_by('-created_at')
    
    # Potential recipients (teachers, directors, librarians, students, parents)
    recipients = User.objects.exclude(id=user.id).order_by('role', 'last_name', 'first_name')

    return render(request, 'school/messages.html', {
        'inbox': inbox,
        'outbox': outbox,
        'recipients': recipients,
    })


@login_required
def schedule_view(request):
    """
    Public and school timetable & bell schedule viewer.
    """
    classes = SchoolClass.objects.all().order_by('number', 'letter')
    class_id = request.GET.get('class_id')

    selected_class = None
    if class_id:
        selected_class = SchoolClass.objects.filter(id=class_id).first()
    elif request.user.is_student and hasattr(request.user, 'student_profile'):
        selected_class = request.user.student_profile.school_class
    
    if not selected_class and classes.exists():
        selected_class = classes.first()

    timetable_by_day = {}
    if selected_class:
        for day_num, day_name in Timetable.DAYS:
            items = Timetable.objects.filter(
                school_class=selected_class, day_of_week=day_num
            ).select_related('subject', 'teacher').order_by('lesson_number')
            timetable_by_day[day_name] = items

    shift1_bells = BellSchedule.objects.filter(shift=1).order_by('lesson_number')
    shift2_bells = BellSchedule.objects.filter(shift=2).order_by('lesson_number')

    return render(request, 'school/schedule.html', {
        'classes': classes,
        'selected_class': selected_class,
        'timetable_by_day': timetable_by_day,
        'shift1_bells': shift1_bells,
        'shift2_bells': shift2_bells,
    })


@login_required
def announcements_view(request):
    """
    All announcements feed.
    """
    user = request.user
    role_q = Q(target_role='all')
    if user.is_student:
        role_q |= Q(target_role='students')
    elif user.is_parent:
        role_q |= Q(target_role='parents')
    elif user.is_teacher:
        role_q |= Q(target_role='teachers')

    announcements = Announcement.objects.filter(role_q).select_related('author', 'target_class').order_by('-is_important', '-created_at')

    # Allow teacher or director to create announcement
    if request.method == 'POST' and (user.is_teacher or user.is_director or user.is_librarian):
        title = request.POST.get('title')
        content = request.POST.get('content')
        target_role = request.POST.get('target_role', 'all')
        is_important = request.POST.get('is_important') == 'on'
        class_id = request.POST.get('target_class')
        target_class = SchoolClass.objects.filter(id=class_id).first() if class_id else None

        if title and content:
            Announcement.objects.create(
                title=title, content=content, author=user,
                target_role=target_role, target_class=target_class, is_important=is_important
            )
            messages.success(request, "Объявление успешно опубликовано!")
            return redirect('school:announcements')

    classes = SchoolClass.objects.all().order_by('number', 'letter')

    return render(request, 'school/announcements.html', {
        'announcements': announcements,
        'classes': classes,
    })
