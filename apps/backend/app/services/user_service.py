"""
TrueShift - User Service

Helpers for consistently resolving authenticated users and canonical IDs.
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserService:
    @staticmethod
    async def resolve_user_by_any_id(db: AsyncSession, user_id: str) -> Optional[User]:
        if not user_id:
            return None

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            return user

        result = await db.execute(select(User).where(User.firebase_uid == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def require_user_by_firebase_uid(db: AsyncSession, firebase_uid: str) -> User:
        result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user


user_service = UserService()
