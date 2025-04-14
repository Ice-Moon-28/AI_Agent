

from typing import Dict

from pydantic import validator
from blog_backend_gpt.type.analysis import AnalysisArguments
from blog_backend_gpt.web.api.agent.tools.list_tools import get_available_tools_names, get_default_tool_name, get_tool_name
from blog_backend_gpt.web.api.agent.tools.search import Search


class Analysis(AnalysisArguments):
    action: str

    @validator("action")
    def action_must_be_valid_tool(cls, v: str) -> str:
        # TODO: Remove circular import
        # 保证模型不会调用未注册的工具
        if v not in get_available_tools_names():
            raise ValueError(f"Analysis action '{v}' is not a valid tool")
        return v

    @validator("action")
    def search_action_must_have_arg(cls, v: str, values: Dict[str, str]) -> str:
        # 保证如果调用搜索工具，必须传搜索关键词
        if v == get_tool_name(Search) and not values["arg"]:
            raise ValueError("Analysis arg cannot be empty if action is 'search'")
        return v

    @classmethod
    def get_default_analysis(cls, task: str) -> "Analysis":
        # TODO: Remove circular import
        # 返回一个默认的分析结果，表示模型无法处理该任务
        return cls(
            reasoning="Hmm... I'll try searching it up",
            action=get_default_tool_name(),
            arg=task,
        )
