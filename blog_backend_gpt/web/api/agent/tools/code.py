from typing import Any

from fastapi.responses import StreamingResponse
from langchain import LLMChain

from blog_backend_gpt.web.api.agent.tools.tools import Tool

from  blog_backend_gpt.web.api.agent.util.prompts import code_prompt


class Code(Tool):
    description = "Should only be used to write code, refactor code, fix code bugs, and explain programming concepts."
    public_description = "Write and review code."

    async def call(
        self, goal: str, task: str, input_str: str, *args: Any, **kwargs: Any
    ) -> StreamingResponse:

        chain = LLMChain(llm=self.model, prompt=code_prompt)

        return StreamingResponse.from_chain(
            chain,
            {"goal": goal, "language": self.language, "task": task},
            media_type="text/event-stream",
        )
