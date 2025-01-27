from typing import Any, Callable, Dict, TypeVar

import langchain
from langchain.chat_models.base import BaseChatModel
from langchain.schema import BaseOutputParser, OutputParserException
from loguru import logger
from openai import (
    AuthenticationError,
    BadRequestError,
    RateLimitError,
    InternalServerError,
)

from blog_backend_gpt.type.agent import ModelSettings
from blog_backend_gpt.web.api.agent.tools.list_tools import get_tool_name
from blog_backend_gpt.web.api.agent.tools.tools import Tool
from blog_backend_gpt.web.errors import OpenAIError


T = TypeVar("T")


def parse_with_handling(parser: BaseOutputParser[T], completion: str) -> T:
    try:
        return parser.parse(completion)
    except OutputParserException as e:
        raise OpenAIError(
            e, "There was an issue parsing the response from the AI model."
        )


async def openai_error_handler(
    func: Callable[..., Any], *args: Any, settings: ModelSettings, **kwargs: Any
) -> Any:
    try:
        return await func(*args, **kwargs)
    except InternalServerError as e:
        raise OpenAIError(
            e,
            "OpenAI is experiencing issues. Visit "
            "https://status.openai.com/ for more info.",
            should_log=not settings.custom_api_key,
        )
    except BadRequestError as e:
        if e.user_message.startswith("The model:"):
            raise OpenAIError(
                e,
                f"Your API key does not have access to your current model. Please use a different model.",
                should_log=not settings.custom_api_key,
            )
        raise OpenAIError(e, e.user_message)
    except AuthenticationError as e:
        raise OpenAIError(
            e,
            "Authentication error: Ensure a valid API key is being used.",
            should_log=not settings.custom_api_key,
        )
    except RateLimitError as e:
        if e.user_message.startswith("You exceeded your current quota"):
            raise OpenAIError(
                e,
                f"Your API key exceeded your current quota, please check your plan and billing details.",
                should_log=not settings.custom_api_key,
            )
        raise OpenAIError(e, e.user_message)
    except Exception as e:
        raise OpenAIError(
            e, "There was an unexpected issue getting a response from the AI model."
        )


async def call_model_with_handling(
    model: BaseChatModel,
    prompt: langchain.BasePromptTemplate,
    args: Dict[str, str],
    settings: ModelSettings,
    **kwargs: Any,
) -> str:
    logger.info(f"Calling model: {model.model_name} {prompt} {args} {kwargs} {settings}")
    chain = prompt | model
    return await openai_error_handler(chain.ainvoke, args, settings=settings, **kwargs)


from typing import Type, TypedDict



class FunctionDescription(TypedDict):
    """Representation of a callable function to the OpenAI API."""

    name: str
    """The name of the function."""
    description: str
    """A description of the function."""
    parameters: dict[str, object]
    """The parameters of the function."""


def get_tool_function(tool: Type[Tool]) -> FunctionDescription:
    """A function that will return the tool's function specification"""
    name = get_tool_name(tool)

    return {
        "name": name,
        "description": tool.description,
        "parameters": {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": (
                        f"Reasoning is how the task will be accomplished with the current function. "
                        "Detail your overall plan along with any concerns you have."
                        "Ensure this reasoning value is in the user defined langauge "
                    ),
                },
                "arg": {
                    "type": "string",
                    "description": tool.arg_description,
                },
            },
            "required": ["reasoning", "arg"],
        },
    }
