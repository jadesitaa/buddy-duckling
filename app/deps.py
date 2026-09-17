from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TokenType, decode_token
from app.db import get_db
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    db: DbSession,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ] = None,
) -> User:
    if credentials is None:
        raise INVALID_CREDENTIALS
    try:
        user_id = decode_token(credentials.credentials, TokenType.ACCESS)
    except jwt.InvalidTokenError:
        raise INVALID_CREDENTIALS from None

    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise INVALID_CREDENTIALS
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
