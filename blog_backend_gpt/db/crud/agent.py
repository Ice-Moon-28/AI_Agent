from fastapi import HTTPException
from loguru import logger
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from blog_backend_gpt.settings import settings
from blog_backend_gpt.db.crud.base import BaseCrud
from blog_backend_gpt.db.orm.agent import AgentRun, AgentTask
from blog_backend_gpt.type.user import UserBase
from blog_backend_gpt.type.LLM import Loop_Step
from blog_backend_gpt.web.errors import MaxLoopsError, MultipleSummaryError

class AgentCRUD(BaseCrud):
    def __init__(self, session: AsyncSession, user: UserBase):
        super().__init__(session)
        self.user = user

    async def create_run(self, goal: str) -> AgentRun:
        return await AgentRun(
            user_id=self.user.id,
            goal=goal,
        ).save(self.session)

    # 检查run任务是否存在，并创建一个新的task任务
    async def create_task(self, run_id: str, type_: Loop_Step) -> AgentTask:
        await self.validate_task_count(run_id, type_)
        return await AgentTask(
            run_id=run_id,
            type_=type_,
        ).save(self.session)

    # 检查当前run任务是否存在，并且检查当前run任务下的task数量是否超过最大限制
    async def validate_task_count(self, run_id: str, type_: str) -> None:
        if not await AgentRun.get(self.session, run_id):
            logger.info(f"Run {run_id} not found")
            raise HTTPException(404, f"Run {run_id} not found")

        query = select(func.count(AgentTask.id)).where(
            and_(
                AgentTask.run_id == run_id,
                AgentTask.type_ == type_,
            )
        )

        task_count = (await self.session.execute(query)).scalar_one()
        max_ = settings.max_loops

        if task_count >= max_:
            raise MaxLoopsError(
                StopIteration(),
                f"Max loops of {max_} exceeded, shutting down.",
                429,
                should_log=False,
            )
        
        ## TODO: 这里的人为的限制是为什么？？？

        if type_ == "summarize" and task_count > 1:
            raise MultipleSummaryError(
                StopIteration(),
                "Multiple summary tasks are not allowed",
                429,
            )
