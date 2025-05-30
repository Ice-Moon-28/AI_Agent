
from typing import Dict, Literal


LLM_Model = Literal[
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    "gpt-4",
    "gpt-4o-mini"
]
Loop_Step = Literal[
    "start",
    "retrieval"
    "analyze",
    "execute",
    "create",
    "summarize",
    "chat",
    
]
LLM_MODEL_MAX_TOKENS: Dict[LLM_Model, int] = {
    "gpt-3.5-turbo": 4000,
    "gpt-3.5-turbo-16k": 16000,
    "gpt-4": 8000,
    "gpt-4o-mini": 10000,
}
