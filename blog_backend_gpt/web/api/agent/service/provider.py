from typing import Any, Callable, Coroutine, Optional

from fastapi import Depends

from blog_backend_gpt.db.crud.oauth import OAuthCrud
from blog_backend_gpt.db.orm.agent import AgentRun
from blog_backend_gpt.db.util.user import get_current_user
from blog_backend_gpt.services.tokenizer.service import TokenService, get_token_service
from blog_backend_gpt.settings import settings
from blog_backend_gpt.type.agent import AgentRunParams
from blog_backend_gpt.type.user import UserBase
from blog_backend_gpt.web.api.agent.model import create_model
from blog_backend_gpt.web.api.agent.service.mock import MockAgentService
from blog_backend_gpt.web.api.agent.service.openai import OpenAIAgentService
from blog_backend_gpt.web.api.agent.service.service import AgentService
from blog_backend_gpt.type.agent import LLM_Model



def get_agent_service(
    validator: Callable[..., Coroutine[Any, Any, AgentRunParams]],
    streaming: bool = False,
    llm_model: Optional[LLM_Model] = None,
) -> Callable[..., AgentService]:
    def func(
        run: AgentRunParams = Depends(validator),
        user: UserBase = Depends(get_current_user),
        token_service: TokenService = Depends(get_token_service),
        oauth_crud: OAuthCrud = Depends(OAuthCrud.inject),
    ) -> AgentService:
        
        
        if settings.ff_mock_mode_enabled:
            return MockAgentService()

        model = create_model(
            settings,
            run.model_settings,
            user,
            streaming=streaming,
            force_model=llm_model,
        )

        return OpenAIAgentService(
            model,
            run.model_settings,
            token_service,
            callbacks=None,
            user=user,
            oauth_crud=oauth_crud,
        )

    return func
