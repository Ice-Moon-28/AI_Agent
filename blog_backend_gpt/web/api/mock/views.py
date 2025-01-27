from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from blog_backend_gpt.db.crud.organization import OrganizationCrud, OrganizationUsers
from blog_backend_gpt.db.orm.user import User, UserSession
from blog_backend_gpt.db.util.session import get_db_session

from sqlalchemy.ext.asyncio import AsyncSession

# from reworkd_platform.db.crud.organization import OrganizationCrud, OrganizationUsers
# from reworkd_platform.schemas import UserBase
# from reworkd_platform.services.oauth_installers import OAuthInstaller, installer_factory
# from reworkd_platform.settings import settings
# from reworkd_platform.web.api.dependencies import get_current_user

router = APIRouter()


@router.post("/users/", response_model=dict)
def create_user(name: str, email: str, db: AsyncSession = Depends(get_db_session)):
    new_user = User(name=name, email=email, create_date=datetime.now())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "name": new_user.name, "email": new_user.email}

@router.post("/sessions/", response_model=dict)
def create_session(user_id: str, token: str, db: AsyncSession = Depends(get_db_session)):
    
    new_session = UserSession(
        session_token=token, user_id=user_id, expires = datetime.now() + timedelta(days=365)
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return {"session_token": new_session.session_token, "user_id": new_session.user_id}