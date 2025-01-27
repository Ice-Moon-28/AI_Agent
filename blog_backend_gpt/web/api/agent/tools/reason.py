from typing import Any

from fastapi.responses import StreamingResponse as FastAPIStreamingResponse
from loguru import logger
from blog_backend_gpt.type.streamResponse import MyStreamingResponse
from blog_backend_gpt.web.api.agent.tools.tools import Tool
from langchain import LLMChain
from blog_backend_gpt.web.api.agent.util.prompts import execute_task_prompt


class Reason(Tool):
    description = (
        "Reason about task via existing information or understanding. "
        "Make decisions / selections from options."
    )

    async def call(
        self, goal: str, task: str, input_str: str, *args: Any, **kwargs: Any
    ) -> FastAPIStreamingResponse:
        
        chain = LLMChain(llm=self.model, prompt=execute_task_prompt)

        logger.info(chain)

        return MyStreamingResponse.from_chain(
            chain,
            {"goal": goal, "language": self.language, "task": task},
            media_type="text/event-stream",
        )
