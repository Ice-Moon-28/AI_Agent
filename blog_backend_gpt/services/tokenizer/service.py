from tiktoken import Encoding, get_encoding


import tiktoken
from fastapi import FastAPI

from blog_backend_gpt.type.LLM import LLM_MODEL_MAX_TOKENS, LLM_Model
from blog_backend_gpt.web.api.agent.model import WrappedChatOpenAI

ENCODING_NAME = "cl100k_base"  # gpt-4, gpt-3.5-turbo, text-embedding-ada-002

from fastapi import Request



def init_tokenizer(app: FastAPI) -> None:  # pragma: no cover
    """
    Initialize tokenizer.

    TikToken downloads the encoding on start. It is then
    stored in the state of the application.

    :param app: current application.
    """
    app.state.token_encoding = tiktoken.get_encoding(ENCODING_NAME)



class TokenService:
    def __init__(self, encoding: Encoding):
        self.encoding = encoding

    @classmethod
    def create(cls, encoding: str = "cl100k_base") -> "TokenService":
        return cls(get_encoding(encoding))

    def tokenize(self, text: str) -> list[int]:
        return self.encoding.encode(text)

    def detokenize(self, tokens: list[int]) -> str:
        return self.encoding.decode(tokens)

    def count(self, text: str) -> int:
        return len(self.tokenize(text))

    def get_completion_space(self, model: LLM_Model, *prompts: str) -> int:
        max_allowed_tokens = LLM_MODEL_MAX_TOKENS.get(model, 4000)
        prompt_tokens = sum([self.count(p) for p in prompts])
        return max_allowed_tokens - prompt_tokens

    def calculate_max_tokens(self, model: WrappedChatOpenAI, *prompts: str) -> None:
        requested_tokens = self.get_completion_space(model.model_name, *prompts)

        model.max_tokens = min(model.max_tokens, requested_tokens)
        model.max_tokens = max(model.max_tokens, 1)

from tiktoken import Encoding, get_encoding


class TokenService:
    def __init__(self, encoding: Encoding):
        self.encoding = encoding

    @classmethod
    def create(cls, encoding: str = "cl100k_base") -> "TokenService":
        return cls(get_encoding(encoding))

    def tokenize(self, text: str) -> list[int]:
        return self.encoding.encode(text)

    def detokenize(self, tokens: list[int]) -> str:
        return self.encoding.decode(tokens)

    def count(self, text: str) -> int:
        return len(self.tokenize(text))

    def count_image_token(self, image_count: int = 1) -> int:
        # same as before
        average_tokens_per_image = 170
        return image_count * average_tokens_per_image

    def get_completion_space(
        self,
        model: LLM_Model,
        *prompts: str,
        image_count: int = 0
    ) -> int:
        max_allowed_tokens = LLM_MODEL_MAX_TOKENS.get(model, 4000)
        prompt_tokens = sum(self.count(p) for p in prompts)
        image_tokens = self.count_image_token(image_count)
        return max_allowed_tokens - prompt_tokens - image_tokens

    def calculate_max_tokens(
        self,
        model: WrappedChatOpenAI,
        *prompts: str,
        image_count: int = 0
    ) -> None:
        """
        Backward‑compatible: you can still do
            calculate_max_tokens(model, prompt_str)
        or, if you want to count a single image:
            calculate_max_tokens(model, prompt_str, image_count=1)
        """
        # collect tokens needed
        requested = self.get_completion_space(model.model_name, *prompts, image_count=image_count)

        # clamp into [1, model.max_tokens]
        model.max_tokens = min(model.max_tokens, requested)
        model.max_tokens = max(model.max_tokens, 1)



def get_token_service(request: Request) -> TokenService:
    return TokenService(request.app.state.token_encoding)

