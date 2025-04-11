from fastapi.routing import APIRouter

from blog_backend_gpt.web.api import auth, monitor, mock, agent
from blog_backend_gpt.web.api.agent.views import router


api_router = APIRouter()
api_router.include_router(monitor.router, prefix="/monitor", tags=["monitoring"])
api_router.include_router(router, prefix="/agent", tags=["agent"])
# api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(mock.router, prefix="/mock", tags=["mocking"])
# api_router.include_router(metadata.router, prefix="/metadata", tags=["metadata"])