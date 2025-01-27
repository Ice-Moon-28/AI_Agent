from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import mapped_column

from blog_backend_gpt.db.base.base import Base

class AgentRun(Base):
    __tablename__ = "agent_run"

    user_id = mapped_column(String(256), nullable=False)
    goal = mapped_column(Text, nullable=False)
    create_date = mapped_column(
        DateTime, name="create_date", server_default=func.now(), nullable=False
    )


class AgentTask(Base):
    __tablename__ = "agent_task"

    run_id = mapped_column(String(256), nullable=False)
    type_ = mapped_column(String(256), nullable=False, name="type")
    create_date = mapped_column(
        DateTime, name="create_date", server_default=func.now(), nullable=False
    )
