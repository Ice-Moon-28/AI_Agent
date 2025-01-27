from ssl import CERT_REQUIRED

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from blog_backend_gpt.settings import settings
from blog_backend_gpt.services.ssl.main import get_ssl_context

def create_engine() -> AsyncEngine:
    """
    Creates SQLAlchemy engine instance.

    :return: SQLAlchemy engine instance.
    """
    if settings.environment == "development":
        return create_async_engine(
            str(settings.db_url),
            echo=settings.db_echo,
        )

    ssl_context = get_ssl_context(settings)
    ssl_context.verify_mode = CERT_REQUIRED
    connect_args = {"ssl": ssl_context}

    return create_async_engine(
        str(settings.db_url),
        echo=settings.db_echo,
        connect_args=connect_args,
    )
