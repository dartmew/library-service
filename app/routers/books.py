from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Book, Rental, User
from ..schemas import BookCreate, BookOut, BookUpdate
from ..security import get_current_user

router = APIRouter(prefix="/books", tags=["books"])


def _available_copies(db: Session, book: Book) -> int:
    active = db.scalar(
        select(func.count(Rental.id)).where(
            Rental.book_id == book.id,
            Rental.returned_at.is_(None),
        )
    )
    return book.total_copies - active


def _to_out(db: Session, book: Book) -> BookOut:
    out = BookOut.model_validate(book)
    out.available_copies = _available_copies(db, book)
    return out


@router.get("", response_model=list[BookOut])
def list_books(
    title: str | None = Query(None, max_length=255),
    author: str | None = Query(None, max_length=255),
    genre: str | None = Query(None, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Book)
    if title:
        stmt = stmt.where(Book.title.ilike(f"%{title}%"))
    if author:
        stmt = stmt.where(Book.author.ilike(f"%{author}%"))
    if genre:
        stmt = stmt.where(Book.genre.ilike(f"%{genre}%"))
    books = db.scalars(stmt.order_by(Book.id).limit(limit).offset(offset)).all()
    return [_to_out(db, b) for b in books]


@router.post("", response_model=BookOut, status_code=201)
def create_book(data: BookCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    book = Book(**data.model_dump())
    db.add(book)
    db.commit()
    db.refresh(book)
    return _to_out(db, book)


@router.get("/{book_id}", response_model=BookOut)
def get_book(book_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    return _to_out(db, book)


@router.patch("/{book_id}", response_model=BookOut)
def update_book(
    book_id: int,
    data: BookUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(book, field, value)
    db.commit()
    db.refresh(book)
    return _to_out(db, book)


@router.delete("/{book_id}", status_code=204)
def delete_book(book_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Книга не найдена")

    active = db.scalar(
        select(func.count(Rental.id)).where(
            Rental.book_id == book_id,
            Rental.returned_at.is_(None),
        )
    )
    if active:
        raise HTTPException(
            status_code=409,
            detail=f"У книги есть активные аренды ({active}), сначала дождитесь возврата",
        )

    db.delete(book)
    db.commit()
