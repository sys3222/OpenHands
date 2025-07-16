from dataclasses import dataclass

from openhands.events.event import Event


@dataclass
class Observation(Event):
    content: str

@dataclass
class UserMessageObservation(Observation):
    """
    This observation is created when the user sends a message.
    """
    pass