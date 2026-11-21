from io import BytesIO

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sqlalchemy import select

from app.models import Book, Rental


def _rentals_df(db) -> pd.DataFrame:
    """Выгружаем аренды с данными о книге в DataFrame."""
    stmt = (
        select(
            Rental.id,
            Rental.book_id,
            Rental.rented_at,
            Rental.due_at,
            Rental.returned_at,
            Book.title,
            Book.author,
            Book.genre,
        )
        .join(Book, Rental.book_id == Book.id)
    )
    return pd.read_sql(stmt, db.bind)


def popularity_top(db, limit: int = 10) -> list[dict]:
    books = pd.read_sql(
        select(Book.id.label("book_id"), Book.title, Book.author),
        db.bind,
    )
    if books.empty:
        return []
    df = _rentals_df(db)
    counts = (
        df.groupby("book_id").size().rename("total_rentals").reset_index()
        if not df.empty
        else pd.DataFrame(columns=["book_id", "total_rentals"])
    )
    out = books.merge(counts, on="book_id", how="left")
    out["total_rentals"] = out["total_rentals"].fillna(0).astype(int)
    out = out.sort_values("total_rentals", ascending=False).head(limit)
    return out.to_dict("records")


def stats_by_genre(db) -> list[dict]:
    books = pd.read_sql(select(Book.id.label("book_id"), Book.genre), db.bind)
    if books.empty:
        return []
    df = _rentals_df(db)
    active = df[df["returned_at"].isna()] if not df.empty else df
    out = books.merge(
        active.groupby("book_id").size().rename("rentals_active").reset_index(),
        on="book_id",
        how="left",
    )
    out["rentals_active"] = out["rentals_active"].fillna(0).astype(int)
    grouped = out.groupby("genre").agg(
        books=("book_id", "nunique"),
        rentals_active=("rentals_active", "sum"),
    ).reset_index()
    return grouped.to_dict("records")


def rental_stats(db) -> dict:
    df = _rentals_df(db)
    stats = {
        "total_rentals": int(len(df)),
        "active_rentals": int(df["returned_at"].isna().sum()) if not df.empty else 0,
        "total_books": int(df["book_id"].nunique()) if not df.empty else 0,
        "avg_rent_days": None,
        "overdue_count": 0,
    }
    if not df.empty:
        returned = df[df["returned_at"].notna()]
        if not returned.empty:
            days = (returned["returned_at"] - returned["rented_at"]).dt.total_seconds() / 86400
            stats["avg_rent_days"] = round(float(days.mean()), 2)
        overdue = df[
            df["due_at"].notna() & df["returned_at"].isna() & (df["due_at"] < pd.Timestamp.now(tz="UTC"))
        ]
        stats["overdue_count"] = int(len(overdue))
    return stats


def plot_popularity(db, limit: int = 10) -> BytesIO:
    df = _rentals_df(db)
    fig, ax = plt.subplots(figsize=(10, 5))
    if df.empty:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center")
    else:
        top = df.groupby("title").size().sort_values(ascending=False).head(limit)
        top.plot(kind="barh", ax=ax, color="#4c72b0")
        ax.invert_yaxis()
        ax.set_title("Топ книг по числу аренд")
        ax.set_xlabel("Количество аренд")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf


def plot_by_genre(db) -> BytesIO:
    books = pd.read_sql(select(Book.id.label("book_id"), Book.genre), db.bind)
    fig, ax = plt.subplots(figsize=(10, 5))
    if books.empty:
        ax.text(0.5, 0.5, "Нет данных", ha="center", va="center")
    else:
        counts = books.groupby("genre").size().sort_values(ascending=False)
        counts.plot(kind="bar", ax=ax, color="#dd8452")
        ax.set_title("Количество книг по жанрам")
        ax.set_ylabel("Книг")
        ax.set_xlabel("")
    fig.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    buf.seek(0)
    return buf
