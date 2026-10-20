from django.db import models
from django.conf import settings
from django.utils import timezone


class SchoolClass(models.Model):
    number = models.PositiveSmallIntegerField(verbose_name="Номер параллели")
    letter = models.CharField(max_length=5, verbose_name="Литера")
    academic_year = models.CharField(max_length=20, default='2026-2027', verbose_name="Учебный год")
    class_teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supervised_classes',
        verbose_name="Классный руководитель"
    )
    shift = models.IntegerField(default=1, choices=[(1, '1-я смена'), (2, '2-я смена')], verbose_name="Смена")

    class Meta:
        verbose_name = "Класс"
        verbose_name_plural = "Классы"
        ordering = ['number', 'letter']
        unique_together = ('number', 'letter', 'academic_year')

    def __str__(self):
        return f"{self.number}-{self.letter}"

    @property
    def name(self):
        return f"{self.number}-{self.letter}"


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название предмета")
    code = models.CharField(max_length=20, blank=True, verbose_name="Код/Аббревиатура")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"
        ordering = ['name']

    def __str__(self):
        return self.name


class TeacherAssignment(models.Model):
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name="Учитель"
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='teacher_assignments',
        verbose_name="Предмет"
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='subject_assignments',
        verbose_name="Класс"
    )

    class Meta:
        verbose_name = "Назначение учителя"
        verbose_name_plural = "Назначения учителей"
        unique_together = ('teacher', 'subject', 'school_class')

    def __str__(self):
        return f"{self.teacher.display_name} — {self.subject.name} ({self.school_class.name})"


class StudentProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name="Пользователь"
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
        verbose_name="Класс"
    )
    date_of_birth = models.DateField(null=True, blank=True, verbose_name="Дата рождения")
    address = models.CharField(max_length=255, blank=True, verbose_name="Домашний адрес")

    class Meta:
        verbose_name = "Профиль ученика"
        verbose_name_plural = "Профили учеников"

    def __str__(self):
        class_str = self.school_class.name if self.school_class else "Без класса"
        return f"{self.user.display_name} ({class_str})"


class TeacherProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        verbose_name="Пользователь"
    )
    qualification = models.CharField(max_length=150, blank=True, verbose_name="Квалификация / Категория")
    cabinet_number = models.CharField(max_length=30, blank=True, verbose_name="Кабинет")
    experience_years = models.PositiveIntegerField(default=1, verbose_name="Стаж (лет)")

    class Meta:
        verbose_name = "Профиль учителя"
        verbose_name_plural = "Профили учителей"

    def __str__(self):
        return f"{self.user.display_name} (Каб. {self.cabinet_number or '—'})"


class BellSchedule(models.Model):
    lesson_number = models.PositiveSmallIntegerField(verbose_name="Номер урока")
    start_time = models.TimeField(verbose_name="Начало")
    end_time = models.TimeField(verbose_name="Конец")
    shift = models.IntegerField(default=1, choices=[(1, '1-я смена'), (2, '2-я смена')], verbose_name="Смена")
    break_duration = models.CharField(max_length=30, blank=True, verbose_name="Перемена (мин)")

    class Meta:
        verbose_name = "Расписание звонков"
        verbose_name_plural = "Расписание звонков"
        ordering = ['shift', 'lesson_number']

    def __str__(self):
        return f"{self.shift} смена | Урок {self.lesson_number}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"


class Timetable(models.Model):
    DAYS = [
        (1, 'Понедельник'),
        (2, 'Вторник'),
        (3, 'Среда'),
        (4, 'Четверг'),
        (5, 'Пятница'),
        (6, 'Суббота'),
    ]
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='timetable_items', verbose_name="Класс")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Учитель")
    day_of_week = models.IntegerField(choices=DAYS, verbose_name="День недели")
    lesson_number = models.PositiveSmallIntegerField(verbose_name="Номер урока")
    room = models.CharField(max_length=50, blank=True, verbose_name="Кабинет")

    class Meta:
        verbose_name = "Урок в расписании"
        verbose_name_plural = "Расписание уроков"
        ordering = ['day_of_week', 'lesson_number']

    def __str__(self):
        return f"{self.school_class.name} | {self.get_day_of_week_display()} | Урок {self.lesson_number}: {self.subject.name}"


class Homework(models.Model):
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name='homeworks', verbose_name="Класс")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='homeworks', verbose_name="Предмет")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_homeworks', verbose_name="Учитель")
    assigned_date = models.DateField(default=timezone.now, verbose_name="Дата задания")
    due_date = models.DateField(verbose_name="Срок сдачи")
    title = models.CharField(max_length=200, verbose_name="Тема задания")
    description = models.TextField(verbose_name="Описание и задания")
    attachment = models.FileField(upload_to='homework_files/', null=True, blank=True, verbose_name="Прикрепленный файл")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Домашнее задание"
        verbose_name_plural = "Домашние задания"
        ordering = ['-due_date', '-created_at']

    def __str__(self):
        return f"{self.school_class.name} - {self.subject.name}: {self.title} (до {self.due_date})"


class Grade(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='grades', verbose_name="Ученик")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='given_grades', verbose_name="Учитель")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='grades', verbose_name="Предмет")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, verbose_name="Класс")
    date = models.DateField(default=timezone.now, verbose_name="Дата")
    grade_value = models.PositiveSmallIntegerField(
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        verbose_name="Оценка"
    )
    comment = models.CharField(max_length=150, blank=True, verbose_name="Тип / Комментарий")
    lesson_number = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Номер урока")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Оценка"
        verbose_name_plural = "Оценки"
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.student.display_name} - {self.subject.name}: {self.grade_value} ({self.date})"


class QuarterGrade(models.Model):
    QUARTERS = [
        (1, 'I четверть'),
        (2, 'II четверть'),
        (3, 'III четверть'),
        (4, 'IV четверть'),
        (5, 'Годовая'),
    ]
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quarter_grades', verbose_name="Ученик")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    quarter = models.PositiveSmallIntegerField(choices=QUARTERS, verbose_name="Четверть / Период")
    academic_year = models.CharField(max_length=20, default='2026-2027', verbose_name="Учебный год")
    grade_value = models.PositiveSmallIntegerField(
        choices=[(2, '2'), (3, '3'), (4, '4'), (5, '5')],
        verbose_name="Итоговая оценка"
    )
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Выставил")

    class Meta:
        verbose_name = "Четвертная/годовая оценка"
        verbose_name_plural = "Четвертные и годовые оценки"
        unique_together = ('student', 'subject', 'quarter', 'academic_year')

    def __str__(self):
        return f"{self.student.display_name} - {self.subject.name} - Q{self.quarter}: {self.grade_value}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('present', 'Был'),
        ('absent', 'Н (Не был)'),
        ('sick', 'Б (Болел)'),
        ('valid', 'УП (Уважительная)'),
    ]
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendances', verbose_name="Ученик")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, verbose_name="Класс")
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Предмет")
    date = models.DateField(default=timezone.now, verbose_name="Дата")
    lesson_number = models.PositiveSmallIntegerField(null=True, blank=True, verbose_name="Номер урока")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='present', verbose_name="Статус посещаемости")
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Учитель")
    notes = models.CharField(max_length=255, blank=True, verbose_name="Примечание")

    class Meta:
        verbose_name = "Посещаемость"
        verbose_name_plural = "Посещаемость"
        ordering = ['-date', 'lesson_number']

    def __str__(self):
        return f"{self.student.display_name} | {self.date} | {self.get_status_display()}"


class Announcement(models.Model):
    TARGET_ROLES = [
        ('all', 'Всей школе'),
        ('students', 'Ученикам'),
        ('parents', 'Родителям'),
        ('teachers', 'Учителям'),
    ]
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Текст объявления")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='announcements', verbose_name="Автор")
    target_role = models.CharField(max_length=20, choices=TARGET_ROLES, default='all', verbose_name="Кому адресовано")
    target_class = models.ForeignKey(SchoolClass, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Для конкретного класса")
    is_important = models.BooleanField(default=False, verbose_name="Важное объявление")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")

    class Meta:
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"
        ordering = ['-is_important', '-created_at']

    def __str__(self):
        return self.title


class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages', verbose_name="Отправитель")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages', verbose_name="Получатель")
    subject = models.CharField(max_length=200, verbose_name="Тема")
    body = models.TextField(verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время отправки")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")

    class Meta:
        verbose_name = "Личное сообщение"
        verbose_name_plural = "Личные сообщения"
        ordering = ['-created_at']

    def __str__(self):
        return f"От {self.sender.display_name} к {self.recipient.display_name}: {self.subject}"


class SchoolNews(models.Model):
    title = models.CharField(max_length=255, verbose_name="Заголовок")
    summary = models.TextField(blank=True, verbose_name="Краткое описание")
    content = models.TextField(verbose_name="Текст новости")
    image = models.ImageField(upload_to='news/', null=True, blank=True, verbose_name="Изображение")
    is_published = models.BooleanField(default=True, verbose_name="Опубликовано")
    published_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")

    class Meta:
        verbose_name = "Школьная новость"
        verbose_name_plural = "Школьные новости"
        ordering = ['-published_at']

    def __str__(self):
        return self.title
