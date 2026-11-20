from fastapi import APIRouter, Depends, Query, Response

from ..database import get_db
from ..models import User
from ..schemas import GenreStat, PopularBook
from ..security import get_current_user
from analytics.reports import plot_popularity, plot_by_genre, popularity_top, rental_stats, stats_by_genre

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/popular", response_model=list[PopularBook])
def popular(limit: int = Query(10, ge=1, le=50), db=Depends(get_db), user: User = Depends(get_current_user)):
    return popularity_top(db, limit)


@router.get("/genres", response_model=list[GenreStat])
def by_genre(db=Depends(get_db), user: User = Depends(get_current_user)):
    return stats_by_genre(db)


@router.get("/stats")
def stats(db=Depends(get_db), user: User = Depends(get_current_user)):
    return rental_stats(db)


@router.get("/popular-plot")
def popular_plot(limit: int = Query(10, ge=1, le=50), db=Depends(get_db), user: User = Depends(get_current_user)):
    buf = plot_popularity(db, limit)
    return Response(content=buf.getvalue(), media_type="image/png")


@router.get("/genres-plot")
def genres_plot(db=Depends(get_db), user: User = Depends(get_current_user)):
    buf = plot_by_genre(db)
    return Response(content=buf.getvalue(), media_type="image/png")
