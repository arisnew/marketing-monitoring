from __future__ import annotations
import logging
import os

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User

logger = logging.getLogger(__name__)


def ensure_default_admin(db: Session) -> None:
    if db.query(User).count() > 0:
        return
    email = os.environ.get("BOOTSTRAP_ADMIN_EMAIL", "admin@example.com")
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "changeme")
    db.add(User(email=email, hashed_password=hash_password(password), role=UserRole.admin))
    db.commit()
    logger.warning("Created bootstrap admin %s — change password immediately", email)
