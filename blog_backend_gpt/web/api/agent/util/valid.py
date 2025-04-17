from typing import TypeVar
from fastapi import Body, Depends
from loguru import logger

from blog_backend_gpt.db.crud.agent import AgentCRUD
from blog_backend_gpt.db.util.session import get_db_session
from blog_backend_gpt.db.util.user import get_current_user
from blog_backend_gpt.type.agent import AgentChat, AgentRunCreateParams, AgentRunParams, AgentSummarize, AgentTaskAnalyzeParams, AgentTaskCreate, AgentTaskExecute, AgentTaskRetrievaleParams
from blog_backend_gpt.type.user import UserBase
from sqlalchemy.ext.asyncio import AsyncSession


from blog_backend_gpt.type.LLM import Loop_Step


def agent_crud(
    user: UserBase = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> AgentCRUD:
    # get current user data and session
    return AgentCRUD(session, user)

T = TypeVar(
    "T", AgentTaskAnalyzeParams, AgentTaskExecute, AgentTaskCreate, AgentSummarize, AgentChat
)


async def validate(body: T, crud: AgentCRUD, type_: Loop_Step) -> T:
    # 存数据库中，创建一个新的任务
    body.run_id = (await crud.create_task(body.run_id, type_)).id
    return body

async def agent_start_validator(
    body: AgentRunCreateParams = Body(
        example={
            "goal": "Create business plan for a bagel company",
            "modelSettings": {
                "customModelName": "gpt-3.5-turbo",
            },
        },
    ),
    crud: AgentCRUD = Depends(agent_crud),
) -> AgentRunParams:
    id_ = (await crud.create_run(body.goal)).id
    logger.info("start_tasks req_body={}, id = {}".format(body.dict(), id_))
    return AgentRunParams(**body.dict(), run_id=str(id_))

# 定义一个异步函数 agent_analyze_validator，用于验证分析任务请求的输入参数
async def agent_analyze_validator(
    body: AgentTaskAnalyzeParams = Body(
        example={
            "goal": "Create business plan for a bagel company",
            "task": "Market research for bagel industry",
            "model_settings": {
                "model": 'gpt-3.5-turbo',
                "custom_api_key": '',
                "temperature": 0.8, 
                "max_tokens": 1250,
                "language": 'English',
            },
            "run_id": '207d2cb2-ace8-4215-b1d9-212b7fd1ce32',
        }
    ),
    crud: AgentCRUD = Depends(agent_crud),
) -> AgentTaskAnalyzeParams:
    return await validate(body, crud, "analyze")

async def agent_execute_validator(
    # 解析对象，example数据用于swagger文档的生成
    body: AgentTaskExecute = Body(
        example={
            "goal": "Create business plan for a bagel company",
            "task": "Market research for bagel industry",
            "analysis": {
                "reasoning": "The best way to gather market research for the bagel industry is to use a search function to find relevant and up-to-date information on market trends, consumer preferences, competitor analysis, and overall industry insights.",
                "arg": "bagel industry market research",
                "action": "search"
            },
            "run_id": '207d2cb2-ace8-4215-b1d9-212b7fd1ce32',
        },
    ),
    crud: AgentCRUD = Depends(agent_crud),
) -> AgentTaskExecute:
    # 创立一个execute数据，如果 run_id 存在，则正常返回
    return await validate(body, crud, "execute")

# 存入一个create task进入agent_task表中
async def agent_create_validator(
    body: AgentTaskCreate = Body(),
    crud: AgentCRUD = Depends(agent_crud),
) -> AgentTaskCreate:
    return await validate(body, crud, "create")


async def agent_summarize_validator(
    body: AgentSummarize = Body(),
    crud: AgentCRUD = Depends(agent_crud),
) -> AgentSummarize:
    return await validate(body, crud, "summarize")


async def agent_chat_validator(
    body: AgentChat = Body(),
    crud: AgentCRUD = Depends(agent_crud),
) -> AgentChat:
    return await validate(body, crud, "chat")

async def agenrt_retrieve_validator(
    body: AgentTaskRetrievaleParams = Body(
        example={
            "goal": "Create business plan for a bagel company",
            "run_id": '207d2cb2-ace8-4215-b1d9-212b7fd1ce32',
        },
    ),
    crud: AgentCRUD = Depends(agent_crud),
) -> AgentTaskRetrievaleParams:
    return await validate(body, crud, "retrieve")