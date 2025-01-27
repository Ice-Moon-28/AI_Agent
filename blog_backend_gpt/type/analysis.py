from typing import Dict

from pydantic import BaseModel, validator


class AnalysisArguments(BaseModel):
    """
    Arguments for the analysis function of a tool. OpenAI functions will resolve these values but leave out the action.
    """

    reasoning: str
    arg: str
