import operator
from typing import Annotated, TypedDict


class AgentState(TypedDict):
    # Using Annotated with operator.add ensure that message
    # are appended to the history rather than replaced.
    messages: Annotated[list[dict], operator.add]
    current_query: str
    documents: list[str]
    plan: list[str]
    status: str
    final_answer: str
