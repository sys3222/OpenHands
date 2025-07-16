# openhands/events/serialization/event.py
import copy
from dataclasses import asdict, is_dataclass
from pydantic import BaseModel
from openhands.events.action.agent import (
    AgentDelegateAction, AgentFinishAction, AgentRejectAction,
    ChangeAgentStateAction, RecallAction, CondensationAction, CondensationRequestAction
)
from openhands.events.action.commands import (
    CmdRunAction, IPythonRunCellAction
)
from openhands.events.action.message import MessageAction
from openhands.events.action.empty import NullAction
from openhands.events.action.action import Action
from openhands.events.observation.observation import (
    Observation, UserMessageObservation
)
from openhands.events.observation.commands import CmdOutputObservation
from openhands.events.observation.error import ErrorObservation
from openhands.events.observation.agent import AgentStateChangedObservation, AgentCondensationObservation, RecallObservation
from openhands.events.observation.delegate import AgentDelegateObservation
from openhands.events.observation.empty import NullObservation

ACTION_TYPE_TO_CLASS = {
    "run": CmdRunAction,
    "message": MessageAction,
    "finish": AgentFinishAction,
    "reject": AgentRejectAction,
    "delegate": AgentDelegateAction,
    "recall": RecallAction,
    "change_agent_state": ChangeAgentStateAction,
    "null": NullAction,
    "condensation": CondensationAction,
    "condensation_request": CondensationRequestAction,
    "run_ipython": IPythonRunCellAction,
}

OBSERVATION_TYPE_TO_CLASS = {
    "run": CmdOutputObservation,
    "error": ErrorObservation,
    "delegate": AgentDelegateObservation,
    "agent_state_changed": AgentStateChangedObservation,
    "null": NullObservation,
    "user_message": UserMessageObservation,
    "condensation": AgentCondensationObservation,
    "recall": RecallObservation,
}

def event_to_dict(event: object) -> dict:
    """
    Converts an event to a dictionary.
    Handles both Pydantic models and dataclasses.
    """
    if isinstance(event, BaseModel):
        return event.model_dump()
    if is_dataclass(event):
        return asdict(event)
    
    if hasattr(event, '__dict__'):
        return event.__dict__
    
    raise TypeError(f"Object of type {type(event).__name__} is not a Pydantic model or dataclass and cannot be converted to a dict.")

def event_from_dict(data: dict) -> Action | Observation:
    """
    Converts a dictionary to an event.
    """
    data = copy.deepcopy(data)
    if 'action' in data:
        action_class = ACTION_TYPE_TO_CLASS.get(data['action'])
        if action_class:
            return action_class(**data)
    elif 'observation' in data:
        obs_class = OBSERVATION_TYPE_TO_CLASS.get(data['observation'])
        if obs_class:
            return obs_class(**data)
    raise ValueError(f"Unknown event type: {data}")

def observation_from_dict(data: dict) -> Observation:
    """
    Converts a dictionary to an observation.
    """
    return event_from_dict(data)

def action_from_dict(data: dict) -> Action:
    """
    Converts a dictionary to an action.
    """
    return event_from_dict(data)

def event_to_trajectory(event: object) -> dict:
    """
    Converts an event to a dictionary for trajectory logging.
    """
    return event_to_dict(event)

def truncate_content(content: str, max_chars: int) -> str:
    """
    Truncates the content of an event to a maximum number of characters.
    """
    if len(content) > max_chars:
        return content[:max_chars] + "..."
    return content