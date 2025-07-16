# openhands/graphs/schemas.py
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class EventSource(Enum):
    AGENT = "agent"
    USER = "user"

class Event(BaseModel):
    """Base class for events in the graph, now using Pydantic."""
    source: EventSource = Field(default=EventSource.AGENT)

    class Config:
        arbitrary_types_allowed = True

class Action(Event):
    """Base class for all actions."""
    action: str = ""
    runnable: bool = Field(default=True, exclude=True)

class Observation(Event):
    """Base class for all observations."""
    pass

class MessageAction(Action):
    action: str = "message"
    content: str
    source: EventSource = Field(default=EventSource.AGENT)

class CmdRunAction(Action):
    action: str = "run"
    command: str
    timeout: Optional[int] = 30

class IPythonRunCellAction(Action):
    action: str = "run"
    code: str

class AgentFinishAction(Action):
    action: str = "finish"
    runnable: bool = Field(default=False, exclude=True)

class AgentDelegateAction(Action):
    action: str = "delegate"
    agent_name: str
    inputs: Dict[str, Any]
    runnable: bool = Field(default=False, exclude=True)

class CmdOutputObservation(Observation):
    content: str
    command: str
    exit_code: int = 0
    command_id: int = 0

class ErrorObservation(Observation):
    content: str = "Error"

class AgentDelegateObservation(Observation):
    outputs: Dict[str, Any]

class AgentCondensationObservation(Observation):
    pass

class NullAction(Action):
    action: str = "null"
    runnable: bool = Field(default=False, exclude=True)

class NullObservation(Observation): pass