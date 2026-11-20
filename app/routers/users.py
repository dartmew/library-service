from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserOut, UserUpdate
from ..security import get_current_admin, get_current_user, hash_password

router = APIRouter(prefix="/users", tags=["users"])


def _ensure_can_access(current: User, target: User) -> None:
    if current.id != target.id and not current.is_admin:
        raise HTTPException(status_code=403, detail="Нет доступа")


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    return db.scalars(select(User).order_by(User.id)).all()


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    _ensure_can_access(user, target)
    return target


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    _ensure_can_access(user, target)
    if data.name is not None:
        target.name = data.name
    db.commit()
    db.refresh(target)
    return target


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Пользователь не найдена" if False else "Пользователь не найден")
    if target.id == admin.id:
        raise HTTPException(status_code=409, detail="Нельзя удалить собственную учётную запись")
    db.delete(target)
    db.commit()
