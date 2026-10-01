from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import RequireAdmin, RequireViewer, get_current_user
from app.models.enums import UserRole
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, Token, UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])


def _active_admin_count(db: Session) -> int:
    return (
        db.query(User)
        .filter(User.role == UserRole.admin, User.is_active.is_(True))
        .count()
    )


def _get_user_or_404(user_id: str, db: Session) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _login_user(email: str, password: str, db: Session) -> Token:
    user = db.query(User).filter(User.email == email).one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return Token(access_token=create_access_token(user.id, user.role))


@router.post("/login", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    return _login_user(form.username, form.password, db)


@router.post("/login/json", response_model=Token)
def login_json(body: LoginRequest, db: Session = Depends(get_db)) -> Token:
    return _login_user(body.email, body.password, db)


@router.get("/me", response_model=UserOut)
def me(user: User = RequireViewer) -> User:
    return user


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = RequireAdmin) -> list[User]:
    return db.query(User).order_by(User.email).all()


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, db: Session = Depends(get_db), _: User = RequireAdmin) -> User:
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=body.email, hashed_password=hash_password(body.password), role=body.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    body: UserUpdate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
    _: User = RequireAdmin,
) -> User:
    user = _get_user_or_404(user_id, db)
    if body.password is not None:
        if len(body.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
        user.hashed_password = hash_password(body.password)

    if body.role is not None:
        if (
            user.role == UserRole.admin
            and user.is_active
            and body.role != UserRole.admin
            and _active_admin_count(db) <= 1
        ):
            raise HTTPException(status_code=400, detail="Cannot remove the last active admin")
        user.role = body.role

    if body.is_active is not None:
        if user.id == actor.id and not body.is_active:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        if (
            user.role == UserRole.admin
            and user.is_active
            and body.is_active is False
            and _active_admin_count(db) <= 1
        ):
            raise HTTPException(status_code=400, detail="Cannot deactivate the last active admin")
        user.is_active = body.is_active

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204, response_class=Response)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
    _: User = RequireAdmin,
) -> Response:
    user = _get_user_or_404(user_id, db)
    if user.id == actor.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    if user.role == UserRole.admin and user.is_active and _active_admin_count(db) <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the last active admin")
    db.delete(user)
    db.commit()
    return Response(status_code=204)
