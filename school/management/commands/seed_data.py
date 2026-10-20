from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date, time
from accounts.models import User, Role, ParentStudentRelation
from school.models import (
    SchoolClass, Subject, TeacherAssignment, StudentProfile, TeacherProfile,
    BellSchedule, Timetable, Grade, QuarterGrade, Attendance, Homework,
    Announcement, Message, SchoolNews
)
from library.models import (
    LibrarySettings, Genre, Book, BookCopy, Reservation, BorrowRecord, BookRecommendation
)


class Command(BaseCommand):
    help = "Seeds initial demo data for school and library portal"

    def handle(self, *args, **options):
        self.stdout.write("Начало генерации данных...")

        # 1. Library Settings
        lib_settings = LibrarySettings.get_settings()
        lib_settings.default_loan_days = 14
        lib_settings.max_books_per_reader = 3
        lib_settings.reservation_validity_days = 3
        lib_settings.save()
        self.stdout.write("[OK] Настройки библиотеки обновлены")

        # 2. Users
        def create_user(username, first_name, last_name, role, email=None, is_superuser=False):
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': role,
                    'email': email or f"{username}@school.edu",
                    'linked_gmail': f"{username}@gmail.com",
                    'is_staff': is_superuser or (role in [Role.DIRECTOR, Role.LIBRARIAN]),
                    'is_superuser': is_superuser,
                }
            )
            user.set_password("password123")
            user.role = role
            user.first_name = first_name
            user.last_name = last_name
            user.linked_gmail = f"{username}@gmail.com"
            user.save()
            return user

        director = create_user("director", "Бакыт", "Асанов", Role.DIRECTOR, is_superuser=True)
        librarian = create_user("librarian", "Елена", "Смирнова", Role.LIBRARIAN)
        teacher1 = create_user("teacher", "Дастан", "Ибраев", Role.TEACHER)
        teacher2 = create_user("teacher2", "Айгуль", "Кожоева", Role.TEACHER)
        teacher3 = create_user("teacher3", "Марат", "Осмонов", Role.TEACHER)
        
        student1 = create_user("student", "Арсен", "Жумабеков", Role.STUDENT)
        student2 = create_user("student2", "Бегимай", "Садыкова", Role.STUDENT)
        student3 = create_user("student3", "Артур", "Ким", Role.STUDENT)
        student4 = create_user("student4", "Динара", "Алиева", Role.STUDENT)

        parent1 = create_user("parent", "Медербек", "Жумабеков", Role.PARENT)
        parent2 = create_user("parent2", "Анара", "Садыкова", Role.PARENT)

        # Parent relations
        ParentStudentRelation.objects.get_or_create(parent=parent1, student=student1, defaults={'relation_type': 'Отец'})
        ParentStudentRelation.objects.get_or_create(parent=parent2, student=student2, defaults={'relation_type': 'Мать'})

        # Teacher profiles
        TeacherProfile.objects.update_or_create(
            user=teacher1,
            defaults={'qualification': 'Учитель высшей категории', 'cabinet_number': '304', 'experience_years': 12}
        )
        TeacherProfile.objects.update_or_create(
            user=teacher2,
            defaults={'qualification': 'Отличник образования КР', 'cabinet_number': '210', 'experience_years': 18}
        )
        TeacherProfile.objects.update_or_create(
            user=teacher3,
            defaults={'qualification': 'Учитель первой категории', 'cabinet_number': '401', 'experience_years': 8}
        )

        self.stdout.write("[OK] Пользователи и профили созданы")

        # 3. Classes
        c9a, _ = SchoolClass.objects.get_or_create(number=9, letter='А', defaults={'class_teacher': teacher1, 'shift': 1})
        c9b, _ = SchoolClass.objects.get_or_create(number=9, letter='Б', defaults={'class_teacher': teacher2, 'shift': 1})
        c10a, _ = SchoolClass.objects.get_or_create(number=10, letter='А', defaults={'class_teacher': teacher3, 'shift': 1})
        c10b, _ = SchoolClass.objects.get_or_create(number=10, letter='Б', defaults={'shift': 2})
        c11a, _ = SchoolClass.objects.get_or_create(number=11, letter='А', defaults={'shift': 1})

        # Student profiles
        StudentProfile.objects.update_or_create(user=student1, defaults={'school_class': c9a, 'date_of_birth': date(2010, 4, 12), 'address': 'ул. Киевская 112, кв. 14'})
        StudentProfile.objects.update_or_create(user=student2, defaults={'school_class': c9a, 'date_of_birth': date(2010, 7, 25), 'address': 'пр. Чуй 45, кв. 3'})
        StudentProfile.objects.update_or_create(user=student3, defaults={'school_class': c9b, 'date_of_birth': date(2010, 2, 19), 'address': 'ул. Токтогула 88'})
        StudentProfile.objects.update_or_create(user=student4, defaults={'school_class': c10a, 'date_of_birth': date(2009, 11, 5), 'address': 'ул. Байтик Баатыра 17'})

        # 4. Subjects
        subjects_data = [
            ("Алгебра", "АЛГ", "Курс школьной алгебры и основ анализа"),
            ("Геометрия", "ГЕО", "Планиметрия и стереометрия"),
            ("Кыргызский язык", "КЫРГ", "Мамлекеттик тил жана адабияты"),
            ("Русский язык", "РУС", "Грамматика и правописание русского языка"),
            ("Литература", "ЛИТ", "Классическая и современная литература"),
            ("Физика", "ФИЗ", "Механика, термодинамика и оптика"),
            ("Химия", "ХИМ", "Неорганическая и органическая химия"),
            ("История", "ИСТ", "История Кыргызстана и всемирная история"),
            ("Английский язык", "АНГЛ", "Иностранный язык: грамматика и разговорная речь"),
            ("Информатика", "ИНФ", "Алгоритмы, программирование и ИКТ"),
        ]
        subjects = {}
        for name, code, desc in subjects_data:
            subj, _ = Subject.objects.get_or_create(name=name, defaults={'code': code, 'description': desc})
            subjects[name] = subj

        # Teacher assignments
        TeacherAssignment.objects.get_or_create(teacher=teacher1, subject=subjects["Алгебра"], school_class=c9a)
        TeacherAssignment.objects.get_or_create(teacher=teacher1, subject=subjects["Геометрия"], school_class=c9a)
        TeacherAssignment.objects.get_or_create(teacher=teacher1, subject=subjects["Алгебра"], school_class=c9b)
        TeacherAssignment.objects.get_or_create(teacher=teacher2, subject=subjects["Литература"], school_class=c9a)
        TeacherAssignment.objects.get_or_create(teacher=teacher2, subject=subjects["Кыргызский язык"], school_class=c9a)
        TeacherAssignment.objects.get_or_create(teacher=teacher3, subject=subjects["Физика"], school_class=c9a)

        # 5. Bell Schedule
        bells = [
            (1, time(8, 0), time(8, 45), 1, "10 мин"),
            (2, time(8, 55), time(9, 40), 1, "15 мин (завтрак)"),
            (3, time(9, 55), time(10, 40), 1, "10 мин"),
            (4, time(10, 50), time(11, 35), 1, "15 мин (обед)"),
            (5, time(11, 50), time(12, 35), 1, "10 мин"),
            (6, time(12, 45), time(13, 30), 1, "10 мин"),
            (7, time(13, 40), time(14, 25), 1, "Конец смены"),
        ]
        for num, st, et, shift, brk in bells:
            BellSchedule.objects.get_or_create(
                lesson_number=num, shift=shift,
                defaults={'start_time': st, 'end_time': et, 'break_duration': brk}
            )

        # 6. Timetable for 9-A
        timetable_9a = [
            # Monday
            (1, 1, subjects["Алгебра"], teacher1, "304"),
            (1, 2, subjects["Русский язык"], teacher2, "210"),
            (1, 3, subjects["Кыргызский язык"], teacher2, "210"),
            (1, 4, subjects["Физика"], teacher3, "401"),
            (1, 5, subjects["Английский язык"], teacher1, "205"),
            # Tuesday
            (2, 1, subjects["Геометрия"], teacher1, "304"),
            (2, 2, subjects["Литература"], teacher2, "210"),
            (2, 3, subjects["История"], teacher3, "102"),
            (2, 4, subjects["Информатика"], teacher1, "Каб. ВТ"),
            # Wednesday
            (3, 1, subjects["Кыргызский язык"], teacher2, "210"),
            (3, 2, subjects["Алгебра"], teacher1, "304"),
            (3, 3, subjects["Химия"], teacher3, "308"),
            (3, 4, subjects["Физика"], teacher3, "401"),
            # Thursday
            (4, 1, subjects["Геометрия"], teacher1, "304"),
            (4, 2, subjects["Русский язык"], teacher2, "210"),
            (4, 3, subjects["Английский язык"], teacher1, "205"),
            (4, 4, subjects["История"], teacher3, "102"),
            # Friday
            (5, 1, subjects["Литература"], teacher2, "210"),
            (5, 2, subjects["Алгебра"], teacher1, "304"),
            (5, 3, subjects["Информатика"], teacher1, "Каб. ВТ"),
            (5, 4, subjects["Физика"], teacher3, "401"),
        ]
        for dow, lnum, subj, tchr, room in timetable_9a:
            Timetable.objects.get_or_create(
                school_class=c9a, day_of_week=dow, lesson_number=lnum,
                defaults={'subject': subj, 'teacher': tchr, 'room': room}
            )

        self.stdout.write("[OK] Расписание и звонки настроены")

        # 7. Grades & Attendance
        today = timezone.now().date()
        for i in range(1, 10):
            d = today - timedelta(days=i)
            if d.weekday() < 5:  # weekdays
                # Grades for student1
                Grade.objects.get_or_create(
                    student=student1, teacher=teacher1, subject=subjects["Алгебра"],
                    school_class=c9a, date=d, lesson_number=1,
                    defaults={'grade_value': 5 if i % 2 == 0 else 4, 'comment': 'Ответ у доски' if i % 2 == 0 else 'Самостоятельная работа'}
                )
                Grade.objects.get_or_create(
                    student=student1, teacher=teacher2, subject=subjects["Литература"],
                    school_class=c9a, date=d, lesson_number=2,
                    defaults={'grade_value': 5, 'comment': 'Анализ стихотворения'}
                )
                # Grades for student2
                Grade.objects.get_or_create(
                    student=student2, teacher=teacher1, subject=subjects["Алгебра"],
                    school_class=c9a, date=d, lesson_number=1,
                    defaults={'grade_value': 4, 'comment': 'Домашнее задание'}
                )
                # Attendance
                Attendance.objects.get_or_create(
                    student=student1, school_class=c9a, subject=subjects["Алгебра"],
                    date=d, lesson_number=1,
                    defaults={'status': 'present', 'teacher': teacher1}
                )

        # One sick absence for student1 to show in stats
        Attendance.objects.update_or_create(
            student=student1, school_class=c9a, date=today - timedelta(days=12), lesson_number=1,
            defaults={'status': 'sick', 'teacher': teacher1, 'notes': 'Справка от врача предоставлена'}
        )
        # One unexcused for student2
        Attendance.objects.update_or_create(
            student=student2, school_class=c9a, date=today - timedelta(days=4), lesson_number=2,
            defaults={'status': 'absent', 'teacher': teacher2, 'notes': 'Опоздал на урок'}
        )

        # Quarter Grades for 9-A
        for subj in [subjects["Алгебра"], subjects["Геометрия"], subjects["Литература"], subjects["Физика"]]:
            QuarterGrade.objects.get_or_create(
                student=student1, subject=subj, quarter=1, academic_year='2026-2027',
                defaults={'grade_value': 5, 'teacher': teacher1}
            )
            QuarterGrade.objects.get_or_create(
                student=student2, subject=subj, quarter=1, academic_year='2026-2027',
                defaults={'grade_value': 4, 'teacher': teacher1}
            )

        # 8. Homeworks
        Homework.objects.get_or_create(
            school_class=c9a, subject=subjects["Алгебра"], teacher=teacher1,
            due_date=today + timedelta(days=2),
            defaults={
                'assigned_date': today,
                'title': 'Квадратные уравнения и теорема Виета',
                'description': 'Параграф 14, прочитать правила. Выполнить номера № 342, 345, 348 (в тетради). Подготовиться к устному опросу.'
            }
        )
        Homework.objects.get_or_create(
            school_class=c9a, subject=subjects["Литература"], teacher=teacher2,
            due_date=today + timedelta(days=3),
            defaults={
                'assigned_date': today,
                'title': 'Образ Петра Гринёва в "Капитанской дочке"',
                'description': 'Написать сочинение-рассуждение (1-1.5 стр.) на тему формирования характера Петра Гринёва под влиянием событий восстания.'
            }
        )
        Homework.objects.get_or_create(
            school_class=c9a, subject=subjects["Физика"], teacher=teacher3,
            due_date=today + timedelta(days=1),
            defaults={
                'assigned_date': today - timedelta(days=1),
                'title': 'Законы Ньютона: решение прикладных задач',
                'description': 'Упражнение 12, задачи 1-4. Повторить второй закон Ньютона.'
            }
        )

        # 9. Announcements & Messages & News
        Announcement.objects.get_or_create(
            title="Осенний школьный субботник и посадка деревьев",
            defaults={
                'content': 'Уважаемые учителя, ученики и родители! В эту субботу состоится общешкольный субботник. Сбор во дворе школы в 9:00. Приветствуется рабочий инвентарь и перчатки.',
                'author': director,
                'target_role': 'all',
                'is_important': True,
            }
        )
        Announcement.objects.get_or_create(
            title="Родительское собрание 9-х классов",
            defaults={
                'content': 'Внимание родителей 9-х классов! В среду в 18:00 в актовом зале состоится собрание по вопросам подготовки к ОРТ и выпускным экзаменам.',
                'author': teacher1,
                'target_role': 'parents',
                'target_class': c9a,
                'is_important': False,
            }
        )
        Announcement.objects.get_or_create(
            title="График работы школьной библиотеки в период каникул",
            defaults={
                'content': 'Библиотека открыта ежедневно с 9:00 до 16:00. Просьба читателям вернуть литературу с истекшим сроком выдачи!',
                'author': librarian,
                'target_role': 'all',
                'is_important': False,
            }
        )

        # Messages
        Message.objects.get_or_create(
            sender=teacher1, recipient=parent1,
            subject="Успеваемость Арсена по математике",
            defaults={
                'body': 'Здравствуйте, Медербек! Хочу отметить отличные успехи Арсена в геометрии. Он прекрасно защитил проект и готов к участию в олимпиаде.',
                'is_read': False,
            }
        )
        Message.objects.get_or_create(
            sender=librarian, recipient=student1,
            subject="Напоминание о возврате книги",
            defaults={
                'body': 'Арсен, напоминаем, что срок выдачи книги "Физика 9 класс" истекает через 2 дня. Пожалуйста, продлите или верните книгу.',
                'is_read': True,
            }
        )

        # News
        SchoolNews.objects.get_or_create(
            title="Победа наших учащихся на районной олимпиаде по точным наукам",
            defaults={
                'summary': 'Команда нашей школы заняла первое общекомандное место на олимпиаде среди 24 школ района.',
                'content': 'Поздравляем учеников 9-11 классов и их наставников с блестящей победой! В олимпиаде по математике, физике и информатике наши ребята завоевали 5 первых мест.',
            }
        )
        SchoolNews.objects.get_or_create(
            title="Открытие обновлённого читального зала школьной библиотеки",
            defaults={
                'summary': 'В читальном зале появились компьютеры с доступом к электронному каталогу и зона для групповых проектов.',
                'content': 'При поддержке попечительского совета и выпускников школы завершён ремонт библиотечного зала. Ждём всех учеников и учителей!',
            }
        )

        # 10. Library: Genres & Books & Copies
        genres_data = [
            ("Художественная литература", "Романы, повести, рассказы"),
            ("Школьные учебники", "Учебники и методические пособия для 1-11 классов"),
            ("Кыргызская классика", "Классические произведения кыргызских писателей"),
            ("Научно-популярная", "Книги о науке, технике, астрономии и природе"),
            ("Фантастика и приключения", "Зарубежная и отечественная фантастика"),
            ("Словари и энциклопедии", "Справочные издания"),
        ]
        genres = {}
        for gname, gdesc in genres_data:
            g, _ = Genre.objects.get_or_create(name=gname, defaults={'description': gdesc})
            genres[gname] = g

        books_data = [
            {
                'title': 'Белый пароход',
                'author': 'Чингиз Айтматов',
                'genre': genres['Кыргызская классика'],
                'grade_level': 8,
                'language': 'ru',
                'publication_year': 2021,
                'isbn': '978-5-17-112345-1',
                'description': 'Повесть о семилетнем мальчике и его дедушке Момуне, живущих на лесном кордоне у озера Иссык-Куль.',
                'is_new': False,
                'copies_count': 5,
            },
            {
                'title': 'Биринчи мугалим (Первый учитель)',
                'author': 'Чыңгыз Айтматов',
                'genre': genres['Кыргызская классика'],
                'grade_level': 7,
                'language': 'kg',
                'publication_year': 2022,
                'isbn': '978-9967-14-111-2',
                'description': 'Дүйшөн аттуу жаш жигиттин айылдагы балдарды билимге үндөгөн эрдиги жана тагдыры тууралуу атактуу повесть.',
                'is_new': True,
                'copies_count': 4,
            },
            {
                'title': 'Манас (Эпос)',
                'author': 'Сагымбай Орозбаков варианты',
                'genre': genres['Кыргызская классика'],
                'grade_level': 9,
                'language': 'kg',
                'publication_year': 2020,
                'isbn': '978-9967-04-990-1',
                'description': 'Кыргыз элинин баатырдык улуу эпосу. Сагымбай Орозбаковдун айтуусундагы академиялык басылышы.',
                'is_new': False,
                'copies_count': 6,
            },
            {
                'title': 'Геометрия 7-9 классы',
                'author': 'Л.С. Атанасян, В.Ф. Бутузов, С.Б. Кадомцев',
                'genre': genres['Школьные учебники'],
                'grade_level': 9,
                'language': 'ru',
                'publication_year': 2023,
                'isbn': '978-5-09-087654-3',
                'description': 'Базовый школьный учебник по планиметрии: треугольники, окружности, векторы, многоугольники.',
                'is_new': False,
                'copies_count': 10,
            },
            {
                'title': 'Алгебра и начала математического анализа 10-11 класс',
                'author': 'Ш.А. Алимов, Ю.М. Колягин',
                'genre': genres['Школьные учебники'],
                'grade_level': 10,
                'language': 'ru',
                'publication_year': 2022,
                'isbn': '978-5-09-074521-9',
                'description': 'Учебник по тригонометрии, производным, интегралам и степенным функциям.',
                'is_new': False,
                'copies_count': 8,
            },
            {
                'title': 'Физика. 9 класс',
                'author': 'А.В. Пёрышкин, Е.М. Гутник',
                'genre': genres['Школьные учебники'],
                'grade_level': 9,
                'language': 'ru',
                'publication_year': 2023,
                'isbn': '978-5-358-22314-5',
                'description': 'Законы взаимодействия и движения тел, механические колебания и волны, электромагнитное поле.',
                'is_new': False,
                'copies_count': 8,
            },
            {
                'title': 'Капитанская дочка',
                'author': 'Александр Пушкин',
                'genre': genres['Художественная литература'],
                'grade_level': 8,
                'language': 'ru',
                'publication_year': 2021,
                'isbn': '978-5-389-07432-8',
                'description': 'Исторический роман, действие которого происходит во время восстания Емельяна Пугачёва.',
                'is_new': False,
                'copies_count': 6,
            },
            {
                'title': 'Гарри Поттер и философский камень',
                'author': 'Дж. К. Роулинг',
                'genre': genres['Фантастика и приключения'],
                'grade_level': 6,
                'language': 'ru',
                'publication_year': 2024,
                'isbn': '978-5-389-07435-9',
                'description': 'Первая книга захватывающей серии о юном волшебнике Гарри Поттере и школе магии Хогвартс.',
                'is_new': True,
                'copies_count': 3,
            },
            {
                'title': 'Краткая история времени',
                'author': 'Стивен Хокинг',
                'genre': genres['Научно-популярная'],
                'grade_level': 10,
                'language': 'ru',
                'publication_year': 2022,
                'isbn': '978-5-17-102341-2',
                'description': 'От Большого взрыва до черных дыр: доступный рассказ о космологии и теории относительности.',
                'is_new': True,
                'copies_count': 4,
            },
            {
                'title': 'Кыргыз тили. 9-класс',
                'author': 'А. Осмонкулов, Б. Мукамбаев',
                'genre': genres['Школьные учебники'],
                'grade_level': 9,
                'language': 'kg',
                'publication_year': 2023,
                'isbn': '978-9967-14-222-1',
                'description': 'Кыргыз тилинин синтаксиси, татаал сүйлөмдөрдүн түрлөрү боюнча мектеп окуу китеби.',
                'is_new': False,
                'copies_count': 12,
            },
        ]

        inv_counter = 100
        created_books = {}
        for b_data in books_data:
            copies_num = b_data.pop('copies_count')
            b, _ = Book.objects.get_or_create(title=b_data['title'], defaults=b_data)
            created_books[b.title] = b
            for c_idx in range(1, copies_num + 1):
                inv = f"INV-2026-{inv_counter}"
                inv_counter += 1
                BookCopy.objects.get_or_create(
                    book=b, inventory_number=inv,
                    defaults={'status': 'available', 'condition': 'good'}
                )

        # 11. Active loans, overdue loans, reservations
        # Student1 has 1 active normal loan, and 1 OVERDUE loan so overdue debtor logic can be visually verified!
        aitmatov_copy = created_books['Белый пароход'].copies.filter(status='available').first()
        if aitmatov_copy:
            aitmatov_copy.status = 'borrowed'
            aitmatov_copy.save()
            BorrowRecord.objects.get_or_create(
                copy=aitmatov_copy, reader=student1,
                defaults={
                    'issued_by': librarian,
                    'borrow_date': today - timedelta(days=20),
                    'due_date': today - timedelta(days=6),  # OVERDUE!
                    'initial_condition': 'good',
                    'notes': 'Учебный проект по литературе'
                }
            )

        geom_copy = created_books['Геометрия 7-9 классы'].copies.filter(status='available').first()
        if geom_copy:
            geom_copy.status = 'borrowed'
            geom_copy.save()
            BorrowRecord.objects.get_or_create(
                copy=geom_copy, reader=student1,
                defaults={
                    'issued_by': librarian,
                    'borrow_date': today - timedelta(days=4),
                    'due_date': today + timedelta(days=10),
                    'initial_condition': 'good'
                }
            )

        # Student2 has 1 active loan
        fiz_copy = created_books['Физика. 9 класс'].copies.filter(status='available').first()
        if fiz_copy:
            fiz_copy.status = 'borrowed'
            fiz_copy.save()
            BorrowRecord.objects.get_or_create(
                copy=fiz_copy, reader=student2,
                defaults={
                    'issued_by': librarian,
                    'borrow_date': today - timedelta(days=2),
                    'due_date': today + timedelta(days=12),
                    'initial_condition': 'excellent'
                }
            )

        # Student3 has a returned past loan
        hp_copy = created_books['Гарри Поттер и философский камень'].copies.filter(status='available').first()
        if hp_copy:
            BorrowRecord.objects.get_or_create(
                copy=hp_copy, reader=student3, return_date=today - timedelta(days=1),
                defaults={
                    'issued_by': librarian,
                    'borrow_date': today - timedelta(days=15),
                    'due_date': today - timedelta(days=1),
                    'initial_condition': 'excellent',
                    'return_condition': 'good'
                }
            )

        # Active reservation for student2 on "Манас"
        manas_book = created_books['Манас (Эпос)']
        Reservation.objects.get_or_create(
            book=manas_book, reader=student2, status='pending',
            defaults={
                'expires_at': timezone.now() + timedelta(days=3)
            }
        )

        # Recommendation by Teacher2
        BookRecommendation.objects.get_or_create(
            teacher=teacher2, book=created_books['Биринчи мугалим (Первый учитель)'], target_class=c9a,
            defaults={'note': 'Рекомендуется для внеклассного чтения в рамках недели кыргызской литературы.'}
        )

        self.stdout.write(self.style.SUCCESS("[OK] Все демо-данные успешно созданы!"))
        self.stdout.write("Логины пользователей:")
        self.stdout.write("  Директор:     director  / password123")
        self.stdout.write("  Библиотекарь: librarian / password123")
        self.stdout.write("  Учитель:      teacher   / password123 (также teacher2, teacher3)")
        self.stdout.write("  Ученик:       student   / password123 (также student2, student3)")
        self.stdout.write("  Родитель:     parent    / password123 (также parent2)")
