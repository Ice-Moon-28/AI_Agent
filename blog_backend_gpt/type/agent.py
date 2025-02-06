from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, validator

from blog_backend_gpt.type.LLM import LLM_MODEL_MAX_TOKENS, LLM_Model
from blog_backend_gpt.web.api.agent.service.analysis import Analysis



class ModelSettings(BaseModel):
    model: LLM_Model = Field(default="gpt-3.5-turbo")
    custom_api_key: Optional[str] = Field(default=None)
    temperature: float = Field(default=0.9, ge=0.0, le=1.0)
    max_tokens: int = Field(default=500, ge=0)
    language: str = Field(default="English")

    @validator("max_tokens")
    def validate_max_tokens(cls, v: float, values: Dict[str, Any]) -> float:
        model = values["model"]
        if v > (max_tokens := LLM_MODEL_MAX_TOKENS[model]):
            raise ValueError(f"Model {model} only supports {max_tokens} tokens")
        return v


class AgentRunCreateParams(BaseModel):
    goal: str
    model_settings: ModelSettings = Field(default=ModelSettings())


class AgentRunParams(AgentRunCreateParams):
    run_id: str = Field(default_factory=lambda: str(uuid4()))

class AgentTaskRetrievaleParams(AgentRunParams):
    task: str

class AgentTaskAnalyzeParams(AgentRunParams):
    task: str
    tool_names: List[str] = Field(default=[])
    model_settings: ModelSettings = Field(default=ModelSettings())



class AgentTaskExecute(AgentRunParams):
    task: str
    analysis: Analysis


class AgentTaskCreate(AgentRunParams):
    tasks: List[str] = Field(default=[])
    last_task: Optional[str] = Field(default=None)
    result: Optional[str] = Field(default=None)
    completed_tasks: List[str] = Field(default=[])


class AgentSummarize(AgentRunParams):
    results: List[str] = Field(default=[])


class AgentChat(AgentRunParams):
    message: str
    results: List[str] = Field(default=[])

class NewTasksResponse(BaseModel):
    run_id: str
    new_tasks: List[str] = Field(alias="newTasks")


class RunCount(BaseModel):
    count: int
    first_run: Optional[datetime]
    last_run: Optional[datetime]
