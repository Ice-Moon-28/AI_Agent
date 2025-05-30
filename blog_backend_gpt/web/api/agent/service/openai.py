from typing import List, Optional

from fastapi.responses import StreamingResponse
from langchain import LLMChain
from langchain.callbacks.base import AsyncCallbackHandler
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate
from langchain.schema import HumanMessage
from loguru import logger
from pydantic import ValidationError

from blog_backend_gpt.db.crud.oauth import OAuthCrud
from blog_backend_gpt.services.tokenizer.service import TokenService
from blog_backend_gpt.type.agent import ModelSettings
from blog_backend_gpt.type.user import UserBase
from blog_backend_gpt.web.api.agent.model import WrappedChatOpenAI
from blog_backend_gpt.web.api.agent.service.analysis import Analysis, AnalysisArguments
from blog_backend_gpt.web.api.agent.service.service import AgentService
from blog_backend_gpt.web.api.agent.tools.list_tools import get_default_tool, get_tool_from_name, get_tool_name, get_user_tools
from blog_backend_gpt.web.api.agent.util.openai_helpers import call_model_with_handling, get_tool_function, openai_error_handler, parse_with_handling
from blog_backend_gpt.web.api.agent.util.prompts import start_goal_prompt, start_goal_with_image_prompt, create_tasks_prompt, analyze_task_prompt, chat_prompt, rag_summarization_prompt
from blog_backend_gpt.web.api.agent.util.summarize import summarize
from blog_backend_gpt.web.api.agent.util.task_parser import TaskOutputParser
from blog_backend_gpt.web.errors import OpenAIError

# An implementation of the AgentService interface for OpenAI models
class OpenAIAgentService(AgentService):
    def __init__(
        self,
        model: WrappedChatOpenAI,
        settings: ModelSettings,
        token_service: TokenService,
        callbacks: Optional[List[AsyncCallbackHandler]],
        user: UserBase,
        oauth_crud: OAuthCrud,
    ):
        self.model = model
        self.settings = settings
        self.token_service = token_service
        self.callbacks = callbacks
        self.user = user
        self.oauth_crud = oauth_crud

    async def start_goal_agent(self, *, goal: str, image_url: Optional[str] = None) -> List[str]:
        # 构造prompt模板, 将用户问题转换为适合查询的问题
        # judge wheather the model is vision model or not
        if image_url:
            prompt = ChatPromptTemplate.from_messages(
            [SystemMessagePromptTemplate(prompt=start_goal_with_image_prompt)]
        )
            prompt_variables = {
                "goal": goal,
                "image_url": image_url,
                "language": self.settings.language,
            }
        else:
            prompt = ChatPromptTemplate.from_messages(
                [SystemMessagePromptTemplate(prompt=start_goal_prompt)]
            )
            prompt_variables = {
                "goal": goal,
                "language": self.settings.language,
            }

        # 更新模型的 max_tokens 参数
        self.token_service.calculate_max_tokens(
            self.model,
            prompt.format_prompt(**prompt_variables).to_string(),
            image_count=1 if image_url else 0,  # 如果有图片，则计算图片的 token 数量
        )

        # 调用模型生成任务清单（task list），通过构造好的 prompt 和调用链，向模型发送请求，并返回生成结果。
        completion = await call_model_with_handling(
            self.model,
            prompt,
            prompt_variables,
            settings=self.settings,
            callbacks=self.callbacks,
            image_url=image_url,  # 如果有图片，则传递图片 URL
        )

        # 解析模型返回的任务清单，返回一个任务列表
        task_output_parser = TaskOutputParser(completed_tasks=[])
        tasks = parse_with_handling(task_output_parser, completion if isinstance(completion, str) else completion.content)

        return tasks

    async def analyze_task_agent(
        self, *, goal: str, task: str, tool_names: List[str]
    ) -> Analysis:
        # return a usable tools list
        user_tools = await get_user_tools(tool_names, self.user, self.oauth_crud)
        # 把用户可用的工具类列表 user_tools 转换为 OpenAI function calling 所需的标准函数描述列表。
        functions = list(map(get_tool_function, user_tools))
        
        # 构造 prompt 模板
        prompt = analyze_task_prompt.format_prompt(
            goal=goal,
            task=task,
            language=self.settings.language,
        )

        # 保证整个上下文（输入的 token + 生成的 token）必须不超过模型的最大 token 限制
        self.token_service.calculate_max_tokens(
            self.model,
            prompt.to_string(),
            str(functions),
        )

        # 调用模型
        message = await openai_error_handler(
            # apredict: 模型类专属调用
            func=self.model.apredict_messages,
            messages=prompt.to_messages(),
            functions=functions,
            settings=self.settings,
            callbacks=self.callbacks,
        )

        # 取出函数调用的参数
        function_call = message.additional_kwargs.get("function_call", {})
        completion = function_call.get("arguments", "")

        try:
            # 返回分析结果
            pydantic_parser = PydanticOutputParser(pydantic_object=AnalysisArguments)
            analysis_arguments = parse_with_handling(pydantic_parser, completion)
            return Analysis(
                action=function_call.get("name", get_tool_name(get_default_tool())),
                **analysis_arguments.dict(),
            )
        except (OpenAIError, ValidationError):
            return Analysis.get_default_analysis(task)

    async def execute_task_agent(
        self,
        *,
        goal: str,
        task: str,
        analysis: Analysis,
    ) -> StreamingResponse:
        # TODO: More mature way of calculating max_tokens
        if self.model.max_tokens > 3000:
            self.model.max_tokens = max(self.model.max_tokens - 1000, 3000)

        tool_class = get_tool_from_name(analysis.action)
        return await tool_class(self.model, self.settings.language).call(
            goal,
            task,
            analysis.arg,
            self.user,
            self.oauth_crud,
        )

    # 让agent 根据上一个任务的结果和当前目标自动生成一个新的子任务
    async def create_tasks_agent(
        self,
        *,
        goal: str,
        tasks: List[str],
        last_task: str,
        result: str,
        completed_tasks: Optional[List[str]] = None,
    ) -> List[str]:
        prompt = ChatPromptTemplate.from_messages(
            [SystemMessagePromptTemplate(prompt=create_tasks_prompt)]
        )

        args = {
            "goal": goal,
            "language": self.settings.language,
            "tasks": "\n".join(tasks),
            "lastTask": last_task,
            "result": result,
        }

        self.token_service.calculate_max_tokens(
            self.model, prompt.format_prompt(**args).to_string()
        )

        completion = await call_model_with_handling(
            self.model, prompt, args, settings=self.settings, callbacks=self.callbacks
        )

        previous_tasks = (completed_tasks or []) + tasks
        return [completion] if completion not in previous_tasks else []

    async def summarize_task_agent(
        self,
        *,
        goal: str,
        results: List[str],
    ) -> StreamingResponse:
        self.model.model_name = "gpt-3.5-turbo-16k"
        self.model.max_tokens = 8000  # Total tokens = prompt tokens + completion tokens

        snippet_max_tokens = 7000  # Leave room for the rest of the prompt
        text_tokens = self.token_service.tokenize("".join(results))
        text = self.token_service.detokenize(text_tokens[0:snippet_max_tokens])
        logger.info(f"Summarizing text: {text}")

        return summarize(
            model=self.model,
            language=self.settings.language,
            goal=goal,
            text=text,
        )

    async def chat(
        self,
        *,
        message: str,
        results: List[str],
    ) -> StreamingResponse:
        self.model.model_name = "gpt-3.5-turbo-16k"
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate(prompt=chat_prompt),
                *[HumanMessage(content=result) for result in results],
                HumanMessage(content=message),
            ]
        )

        self.token_service.calculate_max_tokens(
            self.model,
            prompt.format_prompt(
                language=self.settings.language,
            ).to_string(),
        )

        chain = LLMChain(llm=self.model, prompt=prompt)

        return StreamingResponse.from_chain(
            chain,
            {"language": self.settings.language},
            media_type="text/event-stream",
        )
    
    ## get the related documents
    async def retrieval_document_agent(self, *, goal):
        prompt = ChatPromptTemplate.from_messages(
            [SystemMessagePromptTemplate(prompt=rag_summarization_prompt)]
        )

        self.token_service.calculate_max_tokens(
            self.model,
            prompt.format_prompt(
                goal=goal,
                language=self.settings.language,
            ).to_string(),
        )

        completion = await call_model_with_handling(
            self.model,
            ChatPromptTemplate.from_messages(
                [SystemMessagePromptTemplate(prompt=rag_summarization_prompt)]
            ),
            {"goal": goal, "language": self.settings.language},
            settings=self.settings,
            callbacks=self.callbacks,
        )

        task_output_parser = TaskOutputParser(completed_tasks=[])
        context = parse_with_handling(task_output_parser, completion.content)

        return context