from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date

from accounts.models import User, Role, ParentStudentRelation
from school.models import SchoolClass, Subject, TeacherAssignment, StudentProfile, Grade, QuarterGrade, Attendance, Homework
from library.models import Book, BookCopy, BorrowRecord, Reservation, Genre, LibrarySettings


class SchoolPortalFullWorkflowTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Settings
        self.lib_settings = LibrarySettings.get_settings()
        self.lib_settings.default_loan_days = 14
        self.lib_settings.max_books_per_reader = 3
        self.lib_settings.reservation_validity_days = 3
        self.lib_settings.save()

        # Users
        self.director = User.objects.create_user(username='director', password='password123', role=Role.DIRECTOR, is_staff=True)
        self.librarian = User.objects.create_user(username='librarian', password='password123', role=Role.LIBRARIAN, is_staff=True)
        self.teacher = User.objects.create_user(username='teacher', password='password123', role=Role.TEACHER)
        self.student = User.objects.create_user(username='student', password='password123', role=Role.STUDENT)
        self.parent = User.objects.create_user(username='parent', password='password123', role=Role.PARENT)

        # Relation
        ParentStudentRelation.objects.create(parent=self.parent, student=self.student, relation_type='Отец')

        # School class & profiles
        self.school_class = SchoolClass.objects.create(number=9, letter='А', class_teacher=self.teacher)
        StudentProfile.objects.create(user=self.student, school_class=self.school_class)

        # Subject & Assignment
        self.subject = Subject.objects.create(name='Алгебра')
        TeacherAssignment.objects.create(teacher=self.teacher, subject=self.subject, school_class=self.school_class)

        # Book & copies
        self.genre = Genre.objects.create(name='Художественная литература')
        self.book = Book.objects.create(
            title='Капитанская дочка',
            author='А.С. Пушкин',
            genre=self.genre,
            grade_level=8,
            language='ru'
        )
        self.copy1 = BookCopy.objects.create(book=self.book, inventory_number='INV-TEST-001', status='available')
        self.copy2 = BookCopy.objects.create(book=self.book, inventory_number='INV-TEST-002', status='available')

    # 1. Role-based security & redirect tests
    def test_role_access_control(self):
        # Student trying to access teacher cabinet should be redirected with warning
        self.client.login(username='student', password='password123')
        resp = self.client.get(reverse('school:teacher_cabinet'), follow=True)
        self.assertRedirects(resp, reverse('school:student_cabinet'))

        # Student trying to access librarian cabinet
        resp = self.client.get(reverse('library:librarian_cabinet'), follow=True)
        self.assertRedirects(resp, reverse('school:student_cabinet'))

        # Teacher accessing teacher cabinet -> 200 OK
        self.client.login(username='teacher', password='password123')
        resp = self.client.get(reverse('school:teacher_cabinet'))
        self.assertEqual(resp.status_code, 200)

        # Librarian accessing librarian cabinet -> 200 OK
        self.client.login(username='librarian', password='password123')
        resp = self.client.get(reverse('library:librarian_cabinet'))
        self.assertEqual(resp.status_code, 200)

        # Director accessing director cabinet -> 200 OK
        self.client.login(username='director', password='password123')
        resp = self.client.get(reverse('school:director_cabinet'))
        self.assertEqual(resp.status_code, 200)

    # 2. Electronic Class Journal grading and attendance test
    def test_class_journal_submission(self):
        self.client.login(username='teacher', password='password123')
        today_str = timezone.now().date().isoformat()
        url = reverse('school:class_journal') + f"?class_id={self.school_class.id}&subject_id={self.subject.id}&date={today_str}"

        # Submit grade 5 and attendance 'present'
        post_data = {
            f'grade_{self.student.id}': '5',
            f'comment_{self.student.id}': 'Отличный ответ у доски',
            f'attendance_{self.student.id}': 'present',
        }
        resp = self.client.post(url, post_data, follow=True)
        self.assertEqual(resp.status_code, 200)

        # Verify in DB
        grade = Grade.objects.filter(student=self.student, subject=self.subject, grade_value=5).first()
        self.assertIsNotNone(grade)
        self.assertEqual(grade.comment, 'Отличный ответ у доски')

        att = Attendance.objects.filter(student=self.student, school_class=self.school_class, status='present').first()
        self.assertIsNotNone(att)

    # 3. Homework assignment creation test
    def test_homework_creation(self):
        self.client.login(username='teacher', password='password123')
        due = timezone.now().date() + timedelta(days=3)
        post_data = {
            'school_class': self.school_class.id,
            'subject': self.subject.id,
            'title': 'Квадратные уравнения',
            'description': 'Параграф 14, № 345',
            'due_date': due.isoformat(),
        }
        resp = self.client.post(reverse('school:homework_manage'), post_data, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Homework.objects.filter(title='Квадратные уравнения', school_class=self.school_class).exists())

    # 4. Library full cycle: reservation, issue, return
    def test_library_full_cycle(self):
        # Student reserves book
        self.client.login(username='student', password='password123')
        reserve_url = reverse('library:reserve_book', kwargs={'book_id': self.book.id})
        resp = self.client.post(reserve_url, follow=True)
        self.assertEqual(resp.status_code, 200)

        res = Reservation.objects.filter(book=self.book, reader=self.student, status='pending').first()
        self.assertIsNotNone(res)
        self.assertEqual(res.copy.status, 'reserved')

        # Librarian confirms reservation and issues book
        self.client.login(username='librarian', password='password123')
        cab_url = reverse('library:librarian_cabinet')
        resp = self.client.post(cab_url, {'action': 'fulfill_reservation', 'reservation_id': res.id}, follow=True)
        self.assertEqual(resp.status_code, 200)

        # Verify BorrowRecord created with 14-day loan
        borrow = BorrowRecord.objects.filter(reader=self.student, copy=res.copy, return_date__isnull=True).first()
        self.assertIsNotNone(borrow)
        self.assertEqual(borrow.copy.status, 'borrowed')
        self.assertEqual(borrow.due_date, timezone.now().date() + timedelta(days=14))

        # Librarian accepts return
        resp = self.client.post(cab_url, {
            'action': 'return_book',
            'borrow_id': borrow.id,
            'return_condition': 'good'
        }, follow=True)
        self.assertEqual(resp.status_code, 200)

        borrow.refresh_from_db()
        self.assertIsNotNone(borrow.return_date)
        self.assertEqual(borrow.copy.status, 'available')

    # 5. Overdue debtor rule test: reader with overdue books CANNOT reserve new books!
    def test_overdue_reader_cannot_reserve(self):
        # Create an overdue borrow record for the student
        BorrowRecord.objects.create(
            copy=self.copy1,
            reader=self.student,
            issued_by=self.librarian,
            borrow_date=timezone.now().date() - timedelta(days=20),
            due_date=timezone.now().date() - timedelta(days=5), # Overdue!
            initial_condition='good'
        )

        # Student tries to reserve copy2 of the book
        self.client.login(username='student', password='password123')
        reserve_url = reverse('library:reserve_book', kwargs={'book_id': self.book.id})
        resp = self.client.post(reserve_url, follow=True)

        # Must reject reservation
        self.assertContains(resp, "Бронирование заблокировано! У вас есть просроченная литература")
        self.assertFalse(Reservation.objects.filter(copy=self.copy2).exists())

    # 6. Library Excel Export test
    def test_library_excel_export(self):
        self.client.login(username='librarian', password='password123')
        resp = self.client.get(reverse('library:export_excel'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    # 7. User Data Export test
    def test_user_data_export_json(self):
        self.client.login(username='student', password='password123')
        resp = self.client.get(reverse('accounts:export_data'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/json; charset=utf-8')
        self.assertIn('student', resp.content.decode('utf-8'))

    # 8. Login and Public pages rendering tests
    def test_login_page_renders(self):
        resp = self.client.get(reverse('login'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Авторизация')

    def test_public_pages_render(self):
        for url_name in ['home', 'news_list', 'bells', 'contacts']:
            resp = self.client.get(reverse(url_name))
            self.assertEqual(resp.status_code, 200)

    # 9. All Cabinets & Library Views rendering test
    def test_all_cabinets_and_library_views_render(self):
        # Student views
        self.client.login(username='student', password='password123')
        for url in [
            reverse('school:student_cabinet'),
            reverse('school:schedule'),
            reverse('school:announcements'),
            reverse('school:messages'),
            reverse('accounts:settings'),
            reverse('library:catalog'),
            reverse('library:my_books'),
            reverse('library:book_detail', kwargs={'book_id': self.book.id}),
        ]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, f"Failed on URL: {url}")

        # Parent views
        self.client.login(username='parent', password='password123')
        resp = self.client.get(reverse('school:parent_cabinet'))
        self.assertEqual(resp.status_code, 200)

        # Teacher views
        self.client.login(username='teacher', password='password123')
        for url in [
            reverse('school:teacher_cabinet'),
            reverse('school:class_journal'),
            reverse('school:quarter_grades'),
            reverse('school:homework_manage'),
        ]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, f"Failed on URL: {url}")

        # Librarian views
        self.client.login(username='librarian', password='password123')
        for tab in ['borrows', 'reservations', 'debtors', 'catalog', 'reports', 'rules']:
            url = reverse('library:librarian_cabinet') + f"?tab={tab}"
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, f"Failed on URL: {url}")

        # Director views
        self.client.login(username='director', password='password123')
        for url in [
            reverse('school:director_cabinet'),
            reverse('school:import_users'),
        ]:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, f"Failed on URL: {url}")
