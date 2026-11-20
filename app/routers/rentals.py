from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session


from ..database import get_db
from ..models import Book, Rental, User
from ..schemas import RentalOut
from ..security import get_current_user


RENTAL_DAYS = 14


router = APIRouter(prefix="/rentals", tags=["rentals"])


def _active_count(db: Session, book_id: int) -> int:
    """Сколько активных (невозвращённых) аренд у книги."""
    return db.scalar(
        select(func.count(Rental.id)).where(
            Rental.book_id == book_id,
            Rental.returned_at.is_(None),
        )
    ) or 0


@router.post("/book/{book_id}", response_model=RentalOut, status_code=201)
def rent_book(book_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    if _active_count(db, book.id) >= book.total_copies:
        raise HTTPException(status_code=409, detail="Нет свободных экземпляров")

    existing = db.scalar(
        select(Rental).where(
            Rental.book_id == book_id,
            Rental.user_id == user.id,
            Rental.returned_at.is_(None),
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Книга уже у вас на руках")

    rental = Rental(
        book_id=book_id, 
        user_id=user.id,
        due_at=datetime.now(timezone.utc) + timedelta(days=RENTAL_DAYS))
    db.add(rental)
    db.commit()
    db.refresh(rental)
    return rental


@router.post("/{rental_id}/return", response_model=RentalOut)
def return_book(rental_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rental = db.get(Rental, rental_id)
    if rental is None:
        raise HTTPException(status_code=404, detail="Аренда не найдена")
    if rental.user_id != user.id and not user.is_admin:
        raise HTTPException(status_code=403, detail="Нет доступа")
    if rental.returned_at is not None:
        raise HTTPException(status_code=409, detail="Книга уже возвращена")

    rental.returned_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rental)
    return rental


@router.get("/my", response_model=list[RentalOut])
def my_rentals(
    active: bool | None = Query(None),
    overdue: bool | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Rental).where(Rental.user_id == user.id)
    stmt = _apply_filters(stmt, active, overdue)
    return db.scalars(stmt.order_by(Rental.rented_at.desc())).all()


@router.get("", response_model=list[RentalOut])
def all_rentals(
    active: bool | None = Query(None),
    overdue: bool | None = Query(None),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_user),
):
    if not admin.is_admin:
        raise HTTPException(status_code=403, detail="Требуются права администратора")
    stmt = select(Rental)
    stmt = _apply_filters(stmt, active, overdue)
    return db.scalars(stmt.order_by(Rental.rented_at.desc())).all()


def _apply_filters(stmt, active: bool | None, overdue: bool | None):
    now = datetime.now(timezone.utc)
    if active is True:
        stmt = stmt.where(Rental.returned_at.is_(None))
    elif active is False:
        stmt = stmt.where(Rental.returned_at.is_not(None))
    if overdue is True:
        stmt = stmt.where(
            Rental.returned_at.is_(None),
            Rental.due_at.is_not(None),
            Rental.due_at < now,
        )
    elif overdue is False:
        stmt = stmt.where(
            Rental.returned_at.is_(None),
            Rental.due_at.is_not(None),
            Rental.due_at >= now,
        )
    return stmt
