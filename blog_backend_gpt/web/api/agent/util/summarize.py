from dataclasses import dataclass
from typing import List

from langchain import LLMChain
from langchain.chat_models.base import BaseChatModel
from blog_backend_gpt.type.streamResponse import MyStreamingResponse
from blog_backend_gpt.web.api.agent.util.prompts import summarize_with_sources_prompt, summarize_sid_prompt, summarize_prompt


@dataclass
class CitedSnippet:
    index: int
    text: str
    url: str = ""

    def __repr__(self) -> str:
        """
        The string representation the AI model will see
        """
        return f"{{i: {self.index}, text: {self.text}, url: {self.url}}}"


@dataclass
class Snippet:
    text: str

    def __repr__(self) -> str:
        """
        The string representation the AI model will see
        """
        return f"{{text: {self.text}}}"


def summarize(
    model: BaseChatModel,
    language: str,
    goal: str,
    text: str,
) -> MyStreamingResponse:

    chain = LLMChain(llm=model, prompt=summarize_prompt)

    return MyStreamingResponse.from_chain(
        chain,
        {
            "goal": goal,
            "language": language,
            "text": text,
        },
        media_type="text/event-stream",
    )


def summarize_with_sources(
    model: BaseChatModel,
    language: str,
    goal: str,
    query: str,
    snippets: List[CitedSnippet],
) -> MyStreamingResponse:

    chain = LLMChain(llm=model, prompt=summarize_with_sources_prompt)

    return MyStreamingResponse.from_chain(
        chain,
        {
            "goal": goal,
            "query": query,
            "language": language,
            "snippets": snippets,
        },
        media_type="text/event-stream",
    )


def summarize_sid(
    model: BaseChatModel,
    language: str,
    goal: str,
    query: str,
    snippets: List[Snippet],
) -> MyStreamingResponse:
    chain = LLMChain(llm=model, prompt=summarize_sid_prompt)

    return MyStreamingResponse.from_chain(
        chain,
        {
            "goal": goal,
            "query": query,
            "language": language,
            "snippets": snippets,
        },
        media_type="text/event-stream",
    )
