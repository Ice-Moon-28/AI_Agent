from importlib import metadata

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, UJSONResponse
from loguru import logger

from blog_backend_gpt import settings
from blog_backend_gpt.lifetime import register_shutdown_event, register_startup_event
from blog_backend_gpt.web.errors import PlatformaticError, platformatic_exception_handler
from blog_backend_gpt.web.router import api_router


def get_app() -> FastAPI:
    """
    Get FastAPI application.

    This is the main constructor of an application.

    :return: application.
    """
    # configure_logging()

    app = FastAPI(
        title="Reworkd Platform API",
        version=metadata.version("blog-backend-gpt"),
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        default_response_class=UJSONResponse,
    )
    async def http_exception_handler(request, exc: HTTPException):
        logger.debug(f"HTTP error occurred: {exc.detail} {request}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": f"HTTP error occurred: {exc.detail}"},
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        # allow_origin_regex=settings.allowed_origins_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # # Adds startup and shutdown events.
    register_startup_event(app)
    register_shutdown_event(app)

    # Main router for the API.
    app.include_router(router=api_router, prefix="/api")

    app.exception_handler(PlatformaticError)(platformatic_exception_handler)
    app.exception_handler(HTTPException)(http_exception_handler)


    return app
