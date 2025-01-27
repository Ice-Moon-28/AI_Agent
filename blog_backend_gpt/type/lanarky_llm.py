from abc import abstractmethod
import json
from typing import Any, Union

from blog_backend_gpt.type.register import register_streaming_callback, register_streaming_json_callback, register_websocket_callback

from typing import Any

from pydantic import BaseModel, Field
from starlette.types import Message, Send
from langchain.globals import get_llm_cache
from langchain.callbacks.base import AsyncCallbackHandler
from fastapi import WebSocket

from enum import Enum
from typing import Union

from pydantic import BaseModel


class Sender(str, Enum):
    """Sender of a websocket message."""

    BOT = "bot"
    HUMAN = "human"


class Message(str, Enum):
    """Message types for websocket messages."""

    NULL = ""
    ERROR = "Sorry, something went wrong. Try again."

class StreamingJSONResponse(BaseModel):
    """Streaming JSON response."""

    token: str = ""


class AnswerStreamingJSONResponse(BaseModel):
    """Answer response used when cache is enabled and tokens haven't been streamed.
    Should only be output when on_llm_new_token hasn't been invoked before on_chain_end.
    """

    answer: str = ""  # only returned when langchain.llm_cache is used


class MessageType(str, Enum):
    """Message types for websocket messages."""

    START = "start"
    STREAM = "stream"
    END = "end"
    ERROR = "error"
    INFO = "info"

class WebsocketResponse(BaseModel):
    """Websocket response."""

    sender: Sender
    message: Union[Message, str]
    message_type: MessageType

    class Config:
        use_enum_values = True

SUPPORTED_CHAINS = ["LLMChain", "ConversationChain"]

class AsyncLanarkyCallback(AsyncCallbackHandler, BaseModel):
    """Async Callback handler for FastAPI StreamingResponse."""

    output_key: str = Field(default="answer")

    llm_cache_used: bool = Field(default_factory=lambda: get_llm_cache() is not None)

    @property
    def llm_cache_enabled(self) -> bool:
        """Determine if LLM caching is enabled."""
        return get_llm_cache() is not None

    @property
    def always_verbose(self) -> bool:
        """Whether to call verbose callbacks even if verbose is False."""
        return True

    class Config:
        arbitrary_types_allowed = True

    @abstractmethod
    def _construct_message(self, content: Any) -> Any:  # pragma: no cover
        """Constructs a Message from a string."""
        pass


class AsyncStreamingResponseCallback(AsyncLanarkyCallback):
    """Async Callback handler for StreamingResponse."""

    send: Send = Field(...)

    def _construct_message(self, content: str) -> Message:
        """Constructs a Message from a string."""
        return {
            "type": "http.response.body",
            "body": content.encode("utf-8"),
            "more_body": True,
        }


class AsyncWebsocketCallback(AsyncLanarkyCallback):
    """Async Callback handler for WebsocketConnection."""

    websocket: WebSocket = Field(...)
    response: WebsocketResponse = Field(...)

    def _construct_message(self, content: str) -> dict:
        """Constructs a WebsocketResponse from a string."""
        return {**self.response.dict(), **{"message": content}}


class AsyncStreamingJSONResponseCallback(AsyncStreamingResponseCallback):
    """Async Callback handler for StreamingJSONResponse."""

    send: Send = Field(...)

    def _construct_message(self, content: StreamingJSONResponse) -> Message:
        """Constructs a Message from a dictionary."""
        return {
            "type": "http.response.body",
            "body": json.dumps(
                content.dict(),
                ensure_ascii=False,
                allow_nan=False,
                indent=None,
                separators=(",", ":"),
            ).encode("utf-8"),
            "more_body": True,
        }



@register_streaming_callback(SUPPORTED_CHAINS)
class AsyncLLMChainStreamingCallback(AsyncStreamingResponseCallback):
    """AsyncStreamingResponseCallback handler for LLMChain."""

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        if self.llm_cache_used:  # cache missed (or was never enabled) if we are here
            self.llm_cache_used = False
        message = self._construct_message(token)
        await self.send(message)

    async def on_chain_end(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        """Run when chain ends running."""
        # If the cache was used, we need to send the final answer.
        if self.llm_cache_used and self.output_key in outputs:
            message = self._construct_message(outputs[self.output_key])
            await self.send(message)


@register_websocket_callback(SUPPORTED_CHAINS)
class AsyncLLMChainWebsocketCallback(AsyncWebsocketCallback):
    """AsyncWebsocketCallback handler for LLMChain."""

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        if self.llm_cache_used:  # cache missed (or was never enabled) if we are here
            self.llm_cache_used = False
        message = self._construct_message(token)
        await self.websocket.send_json(message)

    async def on_chain_end(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        """Run when chain ends running."""
        # If the cache was used, we need to send the final answer.
        if self.llm_cache_used and self.output_key in outputs:
            message = self._construct_message(outputs[self.output_key])
            await self.websocket.send_json(message)


@register_streaming_json_callback(SUPPORTED_CHAINS)
class AsyncLLMChainStreamingJSONCallback(AsyncStreamingJSONResponseCallback):
    """AsyncStreamingJSONResponseCallback handler for LLMChain."""

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        if self.llm_cache_used:  # cache missed (or was never enabled) if we are here
            self.llm_cache_used = False
        message = self._construct_message(StreamingJSONResponse(token=token))
        await self.send(message)

    async def on_chain_end(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        """Run when chain ends running."""
        # If the cache was used, we need to send the final answer.
        if self.llm_cache_used and self.output_key in outputs:
            message = self._construct_message(
                AnswerStreamingJSONResponse(answer=outputs[self.output_key])
            )
            await self.send(message)
