from datetime import datetime
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from blog_backend_gpt.db.crud.user import UserCrud
from blog_backend_gpt.db.util.session import get_db_session
from blog_backend_gpt.type.user import UserBase
from blog_backend_gpt.web.response import forbidden


def user_crud(
    session: AsyncSession = Depends(get_db_session),
) -> UserCrud:
    return UserCrud(session)

async def get_current_user(
    x_organization_id: Annotated[str | None, Header()] = None,
    bearer: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    crud:   UserCrud = Depends(user_crud),
) -> UserBase:
    """
    Retrieve the current authenticated user based on the Bearer token.

    This function extracts the session token from the Authorization header,
    verifies its validity and expiration, and then returns the associated user's information.

    Args:
        x_organization_id (str | None): Optional organization ID from request header.
        bearer (HTTPAuthorizationCredentials): Authorization credentials extracted via HTTP Bearer scheme.
        crud (UserCrud): Database CRUD operations handler for users and sessions.

    Returns:
        UserBase: The base information of the authenticated user.
    """
    session_token = bearer.credentials

    try:
        session = await crud.get_user_session(session_token)
    except NoResultFound:
        raise forbidden("Invalid session token: {}".format(session_token))

    if session.expires <= datetime.utcnow():
        raise forbidden("Session token expired")

    return UserBase(
        id=session.user.id,
        name=session.user.name,
        email=session.user.email,
        image=session.user.image,
    )
