
from fastapi import APIRouter, Body, Depends

from blog_backend_gpt.type.agent import AgentChat, AgentRunParams, AgentSummarize, AgentTaskAnalyzeParams, AgentTaskCreate, AgentTaskExecute, AgentTaskRetrievaleParams, NewTasksResponse
from blog_backend_gpt.web.api.agent.service.analysis import Analysis
from blog_backend_gpt.web.api.agent.service.provider import get_agent_service
from blog_backend_gpt.web.api.agent.service.service import AgentService
from blog_backend_gpt.web.api.agent.util.valid import agenrt_retrieve_validator, agent_analyze_validator, agent_chat_validator, agent_create_validator, agent_crud, agent_execute_validator, agent_start_validator, agent_summarize_validator, validate
from fastapi.responses import StreamingResponse as FastAPIStreamingResponse
from loguru import logger
router = APIRouter()


## valid 用户的 session ==> 根据输入的 goal and task 启动一个AgentRun 去记录新任务的run_id ==> 返回 run_id 与 分析出来的 tasks
@router.post(
    "/start",
)
async def start_tasks(
    # create a new run task in the database
    req_body: AgentRunParams = Depends(agent_start_validator),
    agent_service: AgentService = Depends(get_agent_service(agent_start_validator)),
) -> NewTasksResponse:
    new_tasks = await agent_service.start_goal_agent(goal=req_body.goal, image_url=req_body.image_url or None)
    return NewTasksResponse(newTasks=new_tasks, run_id=req_body.run_id)


## valid 用户的 session ==> 启动一个新分析 task任务 ===> 返回分析结果 分析结果为 Analysis 任务
@router.post("/analyze")
async def analyze_tasks(
    # agent_analyze_validator: 验证run任务是否存在，以及在数据库中创造一个task任务
    req_body: AgentTaskAnalyzeParams = Depends(agent_analyze_validator),
    agent_service: AgentService = Depends(get_agent_service(agent_analyze_validator)),
) -> Analysis:
    return await agent_service.analyze_task_agent(
        goal=req_body.goal,
        task=req_body.task or "",
        tool_names=req_body.tool_names or [],
    )



## valid 用户信息 ==> 在对应的 run 任务下面 启动一个新run任务 ==> 用来执行具体的function任务
@router.post("/execute")
async def execute_tasks(    
    req_body: AgentTaskExecute = Depends(agent_execute_validator),
    agent_service: AgentService = Depends(
        get_agent_service(validator=agent_execute_validator, streaming=True),
    ),
) -> FastAPIStreamingResponse:
    return await agent_service.execute_task_agent(
        goal=req_body.goal or "",
        task=req_body.task or "",
        analysis=req_body.analysis,
    )

@router.post("/create")
async def create_tasks(
    req_body: AgentTaskCreate = Depends(agent_create_validator),
    agent_service: AgentService = Depends(get_agent_service(agent_create_validator)),
) -> NewTasksResponse:
    new_tasks = await agent_service.create_tasks_agent(
        goal=req_body.goal,
        tasks=req_body.tasks or [],
        last_task=req_body.last_task or "",
        result=req_body.result or "",
        completed_tasks=req_body.completed_tasks or [],
    )
    return NewTasksResponse(newTasks=new_tasks, run_id=req_body.run_id)


@router.post("/summarize")
async def summarize(
    req_body: AgentSummarize = Depends(agent_summarize_validator),
    agent_service: AgentService = Depends(
        get_agent_service(
            validator=agent_summarize_validator,
            streaming=True,
            llm_model="gpt-3.5-turbo-16k",
        ),
    ),
) -> FastAPIStreamingResponse:
    return await agent_service.summarize_task_agent(
        goal=req_body.goal or "",
        results=req_body.results,
    )


@router.post("/chat")
async def chat(
    req_body: AgentChat = Depends(agent_chat_validator),
    agent_service: AgentService = Depends(
        get_agent_service(
            validator=agent_chat_validator,
            streaming=True,
            llm_model="gpt-3.5-turbo-16k",
        ),
    ),
) -> FastAPIStreamingResponse:
    return await agent_service.chat(
        message=req_body.message,
        results=req_body.results,
    )

@router.post("/retrieve")
async def retrieve_tasks(
    req_body: AgentTaskRetrievaleParams = Depends(agenrt_retrieve_validator),
    agent_service: AgentService = Depends(get_agent_service(agenrt_retrieve_validator)),
) -> Analysis:
    return await agent_service.retrieval_document_agent(
        goal=req_body.goal,
    )