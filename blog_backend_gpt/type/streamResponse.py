"""
Credits:

* `gist@ninely <https://gist.github.com/ninely/88485b2e265d852d3feb8bd115065b1a>`_
* `langchain@#1705 <https://github.com/hwchase17/langchain/discussions/1706>`_
"""
from abc import abstractmethod
import asyncio
import logging
from functools import partial, wraps
from typing import Any, Awaitable, Callable, Optional, Union

import aiohttp
from fastapi.responses import StreamingResponse as _StreamingResponse
from langchain.chains.base import Chain
from starlette.background import BackgroundTask
from starlette.types import Receive, Scope, Send

from blog_backend_gpt.type.lanarky_llm import AsyncStreamingJSONResponseCallback, AsyncStreamingResponseCallback, AsyncWebsocketCallback, AsyncLanarkyCallback
from blog_backend_gpt.type.register import STREAMING_CALLBACKS, STREAMING_JSON_CALLBACKS, WEBSOCKET_CALLBACKS

ERROR_MESSAGE = """Error! Chain type '{chain_type}' is not currently supported by '{callable_name}'.
Available chain types: {chain_types}

To use a custom chain type, you must register a new callback handler.
See the documentation for more details: https://lanarky.readthedocs.io/en/latest/advanced/custom_callbacks.html
"""



def _get_callback(
    chain: Chain,
    override: Optional[str],
    callback_registry: dict[str, Any],
    callable_name: str,
    *args,
    **kwargs
):
    """Base function for getting a callback from a registry.

    Args:
        chain: The chain to get the callback for.
        override: The name of the chain type to use instead of the chain's type.
        callback_registry: The registry to get the callback from.
        callable_name: The name of the callable to use in the error message.
        *args: Positional arguments to pass to the callback.
        **kwargs: Keyword arguments to pass to the callback.
    """
    chain_type = override or chain.__class__.__name__
    try:
        callback = callback_registry[chain_type]
        return callback(*args, **kwargs)
    except KeyError:
        raise KeyError(
            ERROR_MESSAGE.format(
                chain_type=chain_type,
                callable_name=callable_name,
                chain_types="\n".join(list(callback_registry.keys())),
            )
        )


def get_streaming_callback(
    chain: Chain, override: Optional[str] = None, *args, **kwargs
) -> AsyncStreamingResponseCallback:
    """Get the streaming callback for the given chain type."""
    return _get_callback(
        chain,
        override,
        STREAMING_CALLBACKS,
        "AsyncStreamingResponseCallback",
        *args,
        **kwargs
    )


def get_websocket_callback(
    chain: Chain, override: Optional[str] = None, *args, **kwargs
) -> AsyncWebsocketCallback:
    """Get the websocket callback for the given chain type."""
    return _get_callback(
        chain, override, WEBSOCKET_CALLBACKS, "AsyncWebsocketCallback", *args, **kwargs
    )


def get_streaming_json_callback(
    chain: Chain, override: Optional[str] = None, *args, **kwargs
) -> AsyncStreamingJSONResponseCallback:
    """Get the streaming JSON callback for the given chain type."""
    return _get_callback(
        chain,
        override,
        STREAMING_JSON_CALLBACKS,
        "AsyncStreamingJSONResponseCallback",
        *args,
        **kwargs
    )


logger = logging.getLogger(__name__)



def openai_aiosession(func):
    """Decorator to set openai.aiosession for StreamingResponse."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            import openai  # type: ignore
        except ImportError:
            raise ImportError(
                "openai is not installed. Install it with `pip install 'lanarky[openai]'`."
            )

        openai.aiosession.set(aiohttp.ClientSession())
        logger.debug(f"opeanai.aiosession set: {openai.aiosession.get()}")

        try:
            await func(*args, **kwargs)
        finally:
            await openai.aiosession.get().close()
            logger.debug(f"opeanai.aiosession closed: {openai.aiosession.get()}")

    return wrapper


# TODO: create OpenAIStreamingResponse for streaming with OpenAI only
class MyStreamingResponse(_StreamingResponse):
    """StreamingResponse class wrapper for langchain chains."""

    def __init__(
        self,
        chain_executor: Callable[[Send], Awaitable[Any]],
        background: Optional[BackgroundTask] = None,
        **kwargs: Any,
    ) -> None:
        """Constructor method.

        Args:
            chain_executor: function to execute ``chain.acall()``.
            background: A ``BackgroundTask`` object to run in the background.
        """
        super().__init__(content=iter(()), background=background, **kwargs)

        self.chain_executor = chain_executor

    async def listen_for_disconnect(self, receive: Receive) -> None:
        """Listen for client disconnect."""
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                logger.debug("Client disconnected")
                break

    async def stream_response(self, send: Send) -> None:
        """Streams the response."""
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )

        try:
            outputs = await self.chain_executor(send)
            if self.background is not None:
                self.background.kwargs["outputs"] = outputs
        except Exception as e:
            if self.background is not None:
                self.background.kwargs["outputs"] = str(e)
            await send(
                {
                    "type": "http.response.body",
                    "body": str(e).encode(self.charset),
                    "more_body": False,
                }
            )
            return

        await send({"type": "http.response.body", "body": b"", "more_body": False})

    @openai_aiosession
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def wrap(func: Callable[[], Awaitable[None]]) -> None:
            await func()
            raise asyncio.CancelledError

        async def run_tasks():
            stream_response_task = asyncio.create_task(
                wrap(partial(self.stream_response, send))
            )
            listen_for_disconnect_task = asyncio.create_task(
                wrap(partial(self.listen_for_disconnect, receive))
            )

            try:
                await asyncio.gather(stream_response_task, listen_for_disconnect_task)
            except asyncio.CancelledError:
                pass

        await asyncio.create_task(run_tasks())

        if self.background is not None:
            await self.background()

    @staticmethod
    def _create_chain_executor(
        chain: Chain,
        inputs: Union[dict[str, Any], Any],
        as_json: bool = False,
        callback: Optional[AsyncLanarkyCallback] = None,
        **callback_kwargs,
    ) -> Callable[[Send], Awaitable[Any]]:
        """Creates a function to execute ``chain.acall()``.

        Args:
            chain: A ``Chain`` object.
            inputs: Inputs to pass to ``chain.acall()``.
            as_json: Whether to return the outputs as JSON.
            callback_kwargs: Keyword arguments to pass to the callback function.
        """
        if callback is None:
            get_callback_fn = (
                get_streaming_json_callback if as_json else get_streaming_callback
            )
            callback = partial(get_callback_fn, chain)

        async def wrapper(send: Send):
            return await chain.acall(
                inputs=inputs,
                callbacks=[callback(send=send, **callback_kwargs)],
            )

        return wrapper

    @classmethod
    def from_chain(
        cls,
        chain: Chain,
        inputs: Union[dict[str, Any], Any],
        as_json: bool = False,
        background: Optional[BackgroundTask] = None,
        callback: Optional[AsyncLanarkyCallback] = None,
        callback_kwargs: dict[str, Any] = {},
        **kwargs: Any,
    ) -> "StreamingResponse":
        """Creates a ``StreamingResponse`` object from a ``Chain`` object.

        Args:
            chain: A ``Chain`` object.
            inputs: Inputs to pass to ``chain.acall()``.
            as_json: Whether to return the outputs as JSON.
            background: A ``BackgroundTask`` object to run in the background.
            callback: custom callback function to use instead of using the registry.
            callback_kwargs: Keyword arguments to pass to the callback function.
        """
        chain_executor = cls._create_chain_executor(
            chain, inputs, as_json, callback, **callback_kwargs
        )

        return cls(
            chain_executor=chain_executor,
            background=background,
            **kwargs,
        )
