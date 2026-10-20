from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    STUDENT = 'student', 'Ученик'
    PARENT = 'parent', 'Родитель'
    TEACHER = 'teacher', 'Учитель'
    LIBRARIAN = 'librarian', 'Библиотекарь'
    DIRECTOR = 'director', 'Директор'


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name="Роль"
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Номер телефона"
    )
    linked_gmail = models.EmailField(
        blank=True,
        null=True,
        verbose_name="Привязанный Gmail",
        help_text="Для сброса пароля и уведомлений"
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name="Фото профиля"
    )
    preferred_language = models.CharField(
        max_length=10,
        default='ru',
        choices=[
            ('ru', 'Русский'),
            ('kg', 'Кыргызча'),
            ('en', 'English'),
        ],
        verbose_name="Язык интерфейса"
    )
    font_size = models.CharField(
        max_length=10,
        default='normal',
        choices=[
            ('compact', 'Компактный (90%)'),
            ('normal', 'Стандартный (100%)'),
            ('large', 'Крупный (115%)'),
        ],
        verbose_name="Размер текста"
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    @property
    def is_student(self):
        return self.role == Role.STUDENT

    @property
    def is_parent(self):
        return self.role == Role.PARENT

    @property
    def is_teacher(self):
        return self.role == Role.TEACHER

    @property
    def is_librarian(self):
        return self.role == Role.LIBRARIAN

    @property
    def is_director(self):
        return self.role == Role.DIRECTOR or self.is_superuser

    @property
    def role_title(self):
        return dict(Role.choices).get(self.role, self.role)

    @property
    def role_badge_class(self):
        classes = {
            Role.STUDENT: 'badge-student',
            Role.PARENT: 'badge-parent',
            Role.TEACHER: 'badge-teacher',
            Role.LIBRARIAN: 'badge-librarian',
            Role.DIRECTOR: 'badge-director',
        }
        return classes.get(self.role, 'badge-secondary')

    @property
    def display_name(self):
        full = self.get_full_name()
        if full.strip():
            return full
        return self.username

    @property
    def avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return None


class ParentStudentRelation(models.Model):
    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='children_relations',
        verbose_name="Родитель"
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='parent_relations',
        verbose_name="Ученик"
    )
    relation_type = models.CharField(
        max_length=50,
        default='Родитель',
        verbose_name="Тип родства"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Связь родитель-ученик"
        verbose_name_plural = "Связи родителей и учеников"
        unique_together = ('parent', 'student')

    def __str__(self):
        return f"{self.parent.display_name} -> {self.student.display_name} ({self.relation_type})"
