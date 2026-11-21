import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Book, Rental, User
from app.security import hash_password

random.seed(42)

BOOKS = [
    # (title, author, genre, year, total_copies)
    ("Мастер и Маргарита", "М. Булгаков", "классика", 1966, 3),
    ("Преступление и наказание", "Ф. Достоевский", "классика", 1866, 2),
    ("Дюна", "Ф. Герберт", "фантастика", 1965, 2),
    ("451 градус по Фаренгейту", "Р. Брэдбери", "фантастика", 1953, 1),
    ("Сияние", "С. Кинг", "хоррор", 1977, 2),
    ("Убийство в Восточном экспрессе", "А. Кристи", "детектив", 1934, 2),
    ("Двенадцать стульев", "И. Ильф, Е. Петров", "юмор", 1928, 3),
    ("Капитанская дочка", "А. Пушкин", "классика", 1836, 1),
]

USERS = [
    ("anna@test.com", "Анна", False),
    ("boris@test.com", "Борис", False),
    ("vera@test.com", "Вера", False),
    ("grigory@test.com", "Григорий", False),
    ("admin@test.com", "Администратор", True),
]

PASSWORD = "Test1234!"

LOAN_DAYS = 14


def seed() -> None:
    db = SessionLocal()

    if db.scalar(select(User).limit(1)) is not None:
        print("БД уже содержит данные — сеeding пропущен.")
        return

    now = datetime.now(timezone.utc)

    users = []
    for email, name, is_admin in USERS:
        users.append(User(
            email=email,
            hashed_password=hash_password(PASSWORD),
            name=name,
            is_admin=is_admin,
            created_at=now - timedelta(days=60),
        ))
    db.add_all(users)

    books = [Book(title=t, author=a, genre=g, year=y, total_copies=c)
             for t, a, g, y, c in BOOKS]
    db.add_all(books)
    db.commit()

    # --- аренды: три сценария на выбор из трёх соседних книг ---
    patterns = ["active", "returned_on_time", "returned_late"]
    rentals = []

    for i in range(18):
        pattern = patterns[i % 3]
        user = random.choice(users)
        book = books[i % len(books)]

        if pattern == "active" and any(
            r.book_id == book.id and r.returned_at is None for r in rentals
        ):
            pattern = "returned_on_time"

        rented_at = now - timedelta(days=random.randint(5, 45))
        rental = Rental(
            book_id=book.id,
            user_id=user.id,
            rented_at=rented_at,
            due_at=rented_at + timedelta(days=LOAN_DAYS),
        )

        if pattern == "active":
            pass
        elif pattern == "returned_on_time":
            rental.returned_at = rented_at + timedelta(days=random.randint(3, LOAN_DAYS - 1))
        else:  # returned_late
            rental.returned_at = rental.due_at + timedelta(days=random.randint(1, 20))

        rentals.append(rental)

    db.add_all(rentals)
    db.commit()

    print(f"Готово: {len(users)} пользователей, {len(books)} книг, {len(rentals)} аренд.")
    print(f"Пароль для всех демо-аккаунтов: {PASSWORD}")
    print(f"Админ: admin@test.com")
    db.close()


if __name__ == "__main__":
    seed()
