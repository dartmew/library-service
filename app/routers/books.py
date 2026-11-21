from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Book, Rental, User
from ..schemas import BookCreate, BookOut, BookUpdate, Page
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


def _to_out_many(db: Session, books: list[Book]) -> list[BookOut]:
    ids = [b.id for b in books]
    counts: dict[int, int] = {}
    if ids:
        rows = db.execute(
            select(Rental.book_id, func.count(Rental.id))
            .where(Rental.book_id.in_(ids), Rental.returned_at.is_(None))
            .group_by(Rental.book_id)
        ).all()
        counts = dict(rows)

    result = []
    for b in books:
        out = BookOut.model_validate(b)
        out.available_copies = b.total_copies - counts.get(b.id, 0)
        result.append(out)
    return result

def _to_out(db: Session, book: Book) -> BookOut:
    return _to_out_many(db, [book])[0]


@router.get("", response_model=Page[BookOut])
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

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    books = db.scalars(stmt.order_by(Book.id).limit(limit).offset(offset)).all()

    return Page(
        total=total,
        limit=limit,
        offset=offset,
        items=_to_out_many(db, list(books)),
    )


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
