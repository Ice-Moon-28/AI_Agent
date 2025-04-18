# from fastapi import APIRouter
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy import select
from datetime import datetime, timedelta

from blog_backend_gpt.db.orm.user import User, UserSession
from blog_backend_gpt.db.util.session import get_db_session

router = APIRouter()


@router.get("/health")
def health_check() -> None:
    """
    Checks the health of a project.

    It returns 200 if the project is healthy.
    """


@router.get("/error")
def error_check() -> None:
    """
    Checks that errors are being correctly logged.
    """
    raise Exception("This is an expected error from the error check endpoint!")

@router.post("/seed-user")
async def seed_test_user(session: AsyncSession = Depends(get_db_session)):
    # 设定用户 & token 信息
    test_user_id = "test-user-id"
    test_email = "test@example.com"
    test_token = "test-token-abc123"

    # 检查用户是否已存在（避免重复插入）
    result = await session.execute(
        select(User).where(User.id == test_user_id)
    )
    user_exists = result.scalar() is not None

    if user_exists:
        return {"msg": "User already seeded."}

    # 创建用户
    user = User(
        id=test_user_id,
        name="Test User",
        email=test_email,
        image="",
        email_verified=datetime.utcnow(),
    )
    session.add(user)

    # 创建 session（有效期设置为100天后）
    user_session = UserSession(
        session_token=test_token,
        user_id=test_user_id,
        expires=datetime.utcnow() + timedelta(days=100),
    )
    session.add(user_session)

    await session.commit()
    return {
        "msg": "Seeded test user and session.",
        "token": test_token,
        "note": "Use this token in Swagger with Bearer prefix.",
    }