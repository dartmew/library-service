from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=100)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    name: str
    is_admin: bool
    created_at: datetime


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class BookCreate(BaseModel):
    title: str = Field(max_length=255)
    author: str = Field(max_length=255)
    genre: str = Field(max_length=100)
    year: int | None = None
    total_copies: int = Field(default=1, ge=1)


class BookUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    author: str | None = Field(default=None, max_length=255)
    genre: str | None = Field(default=None, max_length=100)
    year: int | None = None
    total_copies: int | None = Field(default=None, ge=1)


class BookOut(BookCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    available_copies: int = 0
    created_at: datetime


class RentalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    user_id: int
    rented_at: datetime
    due_at: datetime | None
    returned_at: datetime | None


class GenreStat(BaseModel):
    genre: str
    books: int
    rentals_active: int


class PopularBook(BaseModel):
    book_id: int
    title: str
    author: str
    total_rentals: int


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    total: int
    limit: int
    offset: int
    items: list[T]