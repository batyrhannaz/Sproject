from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class LibrarySettings(models.Model):
    default_loan_days = models.PositiveIntegerField(
        default=14,
        verbose_name="Срок выдачи по умолчанию (дней)"
    )
    max_books_per_reader = models.PositiveIntegerField(
        default=3,
        verbose_name="Лимит книг на читателя"
    )
    reservation_validity_days = models.PositiveIntegerField(
        default=3,
        verbose_name="Срок действия брони (дней)"
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Настройки библиотеки"
        verbose_name_plural = "Настройки библиотеки"

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return f"Правила библиотеки: выдача {self.default_loan_days} дн., лимит {self.max_books_per_reader} шт., бронь {self.reservation_validity_days} дн."


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Жанр / Категория")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Жанр книги"
        verbose_name_plural = "Жанры книг"
        ordering = ['name']

    def __str__(self):
        return self.name


class Book(models.Model):
    LANG_CHOICES = [
        ('ru', 'Русский'),
        ('kg', 'Кыргызча'),
        ('en', 'Английский'),
    ]
    GRADE_CHOICES = [(i, f"{i} класс") for i in range(1, 12)]

    title = models.CharField(max_length=255, verbose_name="Название книги")
    author = models.CharField(max_length=255, verbose_name="Автор")
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True, related_name='books', verbose_name="Жанр")
    grade_level = models.PositiveSmallIntegerField(null=True, blank=True, choices=GRADE_CHOICES, verbose_name="Рекомендуемый класс")
    language = models.CharField(max_length=10, choices=LANG_CHOICES, default='ru', verbose_name="Язык")
    publication_year = models.PositiveIntegerField(null=True, blank=True, verbose_name="Год издания")
    isbn = models.CharField(max_length=30, blank=True, verbose_name="ISBN")
    description = models.TextField(blank=True, verbose_name="Описание / Аннотация")
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True, verbose_name="Обложка")
    is_new = models.BooleanField(default=False, verbose_name="Новинка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Добавлена в базу")

    class Meta:
        verbose_name = "Книга"
        verbose_name_plural = "Книги"
        ordering = ['title']

    def __str__(self):
        return f"{self.title} — {self.author}"

    @property
    def total_copies_count(self):
        return self.copies.exclude(status='written_off').count()

    @property
    def available_copies_count(self):
        return self.copies.filter(status='available').count()

    @property
    def borrowed_copies_count(self):
        return self.copies.filter(status='borrowed').count()

    @property
    def reserved_copies_count(self):
        return self.copies.filter(status='reserved').count()

    @property
    def total_borrow_times(self):
        return BorrowRecord.objects.filter(copy__book=self).count()

    @property
    def status_display(self):
        if self.available_copies_count > 0:
            return "В наличии"
        elif self.reserved_copies_count > 0:
            return "Забронирована"
        elif self.borrowed_copies_count > 0:
            return "Выдана"
        else:
            return "Нет в наличии"

    @property
    def status_badge_class(self):
        if self.available_copies_count > 0:
            return "badge-success"
        elif self.reserved_copies_count > 0:
            return "badge-warning"
        elif self.borrowed_copies_count > 0:
            return "badge-danger"
        return "badge-secondary"

    @property
    def cover_url(self):
        if self.cover_image and hasattr(self.cover_image, 'url'):
            return self.cover_image.url
        return None


class BookCopy(models.Model):
    STATUS_CHOICES = [
        ('available', 'В наличии'),
        ('reserved', 'Забронирован'),
        ('borrowed', 'Выдан'),
        ('written_off', 'Списан'),
    ]
    CONDITION_CHOICES = [
        ('excellent', 'Отличное'),
        ('good', 'Хорошее'),
        ('fair', 'Удовлетворительное'),
        ('poor', 'Ветхое / требует ремонта'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies', verbose_name="Книга")
    inventory_number = models.CharField(max_length=50, unique=True, verbose_name="Инвентарный номер")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available', verbose_name="Статус")
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good', verbose_name="Состояние")
    added_date = models.DateField(auto_now_add=True, verbose_name="Дата поступления")
    notes = models.TextField(blank=True, verbose_name="Примечания")

    class Meta:
        verbose_name = "Экземпляр книги"
        verbose_name_plural = "Экземпляры книг"
        ordering = ['inventory_number']

    def __str__(self):
        return f"{self.book.title} (№ {self.inventory_number})"


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает выдачи'),
        ('confirmed', 'Подтверждена'),
        ('fulfilled', 'Выдана'),
        ('cancelled', 'Отменена'),
        ('expired', 'Истекла'),
    ]

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='reservations', verbose_name="Книга")
    reader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='book_reservations', verbose_name="Читатель")
    copy = models.ForeignKey(BookCopy, on_delete=models.SET_NULL, null=True, blank=True, related_name='reservations', verbose_name="Выделенный экземпляр")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус брони")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата бронирования")
    expires_at = models.DateTimeField(verbose_name="Истекает")

    class Meta:
        verbose_name = "Бронь книги"
        verbose_name_plural = "Бронирования книг"
        ordering = ['-created_at']

    def __str__(self):
        return f"Бронь: {self.reader.display_name} -> {self.book.title} ({self.get_status_display()})"

    @property
    def is_active(self):
        return self.status in ['pending', 'confirmed'] and timezone.now() <= self.expires_at


class BorrowRecord(models.Model):
    copy = models.ForeignKey(BookCopy, on_delete=models.CASCADE, related_name='borrow_records', verbose_name="Экземпляр")
    reader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='borrow_records', verbose_name="Читатель")
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_borrows', verbose_name="Выдал библиотекарь")
    borrow_date = models.DateField(default=timezone.now, verbose_name="Дата выдачи")
    due_date = models.DateField(verbose_name="Срок возврата")
    return_date = models.DateField(null=True, blank=True, verbose_name="Фактическая дата возврата")
    initial_condition = models.CharField(max_length=20, choices=BookCopy.CONDITION_CHOICES, default='good', verbose_name="Состояние при выдаче")
    return_condition = models.CharField(max_length=20, choices=BookCopy.CONDITION_CHOICES, blank=True, verbose_name="Состояние при возврате")
    reservation = models.ForeignKey(Reservation, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Связанная бронь")
    notes = models.TextField(blank=True, verbose_name="Примечания")

    class Meta:
        verbose_name = "Выдача книги"
        verbose_name_plural = "Выдачи книг"
        ordering = ['-borrow_date', '-id']

    def __str__(self):
        return f"Выдача №{self.id}: {self.copy.book.title} -> {self.reader.display_name}"

    @property
    def is_returned(self):
        return self.return_date is not None

    @property
    def is_overdue(self):
        if self.return_date:
            return False
        return timezone.now().date() > self.due_date

    @property
    def days_overdue(self):
        if not self.is_overdue:
            return 0
        return (timezone.now().date() - self.due_date).days


class BookRecommendation(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recommended_books', verbose_name="Учитель")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='recommendations', verbose_name="Книга")
    target_class = models.ForeignKey('school.SchoolClass', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Класс")
    note = models.TextField(verbose_name="Комментарий учителя к рекомендации")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Рекомендация книги"
        verbose_name_plural = "Рекомендации книг"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.teacher.display_name} рекомендует: {self.book.title}"
