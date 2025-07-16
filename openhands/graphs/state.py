# openhands/graphs/state.py
from typing import TypedDict, List, Annotated
from operator import add
from openhands.graphs.schemas import Action, Event

# The Annotated type hint with `add` allows the values of this key to be 
# appended to, rather than overwritten, in each step.
class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        history: A flat list of all events (Actions, Observations, etc.).
        replay_history: A list of events to be replayed.
        is_replay: A flag to indicate if the graph is in replay mode.
        latest_action: The most recent action taken by the agent.
        error: Any error that has occurred.
    """
    history: Annotated[List[Event], add]
    replay_history: List[Action]
    is_replay: bool
    latest_action: Action | None
    error: str | None