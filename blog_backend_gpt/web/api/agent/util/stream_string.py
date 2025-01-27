import asyncio
from typing import AsyncGenerator
from fastapi.responses import StreamingResponse
import tiktoken


async def stream_generator(data: str, delayed: bool) -> AsyncGenerator[bytes, None]:
    if delayed:
        encoding = tiktoken.get_encoding("cl100k_base")
        token_data = encoding.encode(data)

        for token in token_data:
            yield encoding.decode([token]).encode("utf-8")
            await asyncio.sleep(0.025)  # simulate slow processing
    else:
        yield data.encode()


def stream_string(data: str, delayed: bool = False) -> StreamingResponse:
    return StreamingResponse(
        stream_generator(data, delayed),
    )