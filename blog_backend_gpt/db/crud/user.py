from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.orm import selectinload

from blog_backend_gpt.db.crud.base import BaseCrud
from blog_backend_gpt.db.orm.auth import OrganizationUser
from blog_backend_gpt.db.orm.user import UserSession


class UserCrud(BaseCrud):
    async def get_user_session(self, token: str) -> UserSession:
        query = (
            select(UserSession)
            .filter(UserSession.session_token == token)
            .options(selectinload(UserSession.user))
        )
        return (await self.session.execute(query)).scalar_one()

    async def get_user_organization(
        self, user_id: str, organization_id: str
    ) -> Optional[OrganizationUser]:
        query = select(OrganizationUser).filter(
            and_(
                OrganizationUser.user_id == user_id,
                OrganizationUser.organization_id == organization_id,
            )
        )

        # TODO: Only returns the first organization
        return (await self.session.execute(query)).scalar()
