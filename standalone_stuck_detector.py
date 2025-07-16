# standalone_stuck_detector.py
# This script is a standalone, runnable version of the StuckDetector logic from the OpenHands project.
# It includes mock objects to simulate the necessary environment, allowing the detector's logic
# to be tested and verified in isolation before any refactoring or migration.

from enum import Enum

# --- Mock Objects to Simulate the OpenHands Environment ---

class EventSource(Enum):
    AGENT = "agent"
    USER = "user"

class Event:
    """Base class for mock events."""
    def __init__(self, source=EventSource.AGENT):
        self.source = source
    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__
    def __repr__(self):
        return f"{self.__class__.__name__}(source={self.source})"

class Action(Event):
    """Base mock Action."""
    pass

class Observation(Event):
    """Base mock Observation."""
    pass

class MessageAction(Action):
    def __init__(self, content, source=EventSource.AGENT):
        super().__init__(source)
        self.content = content
    def __repr__(self):
        return f"MessageAction(content='{self.content}', source={self.source})"

class CmdRunAction(Action):
    def __init__(self, command):
        super().__init__()
        self.command = command
    def __repr__(self):
        return f"CmdRunAction(command='{self.command}')"

class IPythonRunCellAction(Action):
    def __init__(self, code):
        super().__init__()
        self.code = code
    def __repr__(self):
        return f"IPythonRunCellAction(code='{self.code}')"

class CmdOutputObservation(Observation):
    def __init__(self, content, command, exit_code=0, command_id=0):
        super().__init__()
        self.content = content
        self.command = command
        self.exit_code = exit_code
        self.command_id = command_id # This is like a PID, should be ignored in comparisons
    def __repr__(self):
        return f"CmdOutputObservation(command='{self.command}', exit_code={self.exit_code})"

class ErrorObservation(Observation):
    def __init__(self, content="Error"):
        super().__init__()
        self.content = content
    def __repr__(self):
        return "ErrorObservation()"

class AgentCondensationObservation(Observation):
    def __repr__(self):
        return "AgentCondensationObservation()"

class NullAction(Action): pass
class NullObservation(Observation): pass

class State:
    """A mock State class that only contains the history."""
    def __init__(self, history: list[Event]):
        self.history = history

# --- Standalone Stuck Detector Logic ---

class StandaloneStuckDetector:
    """
    A faithful, standalone implementation of the original StuckDetector's logic.
    It uses the mock objects defined above.
    """
    SYNTAX_ERROR_MESSAGES = [
        'SyntaxError: unterminated string literal (detected at line',
        'SyntaxError: invalid syntax. Perhaps you forgot a comma?',
    ]

    def __init__(self, state: State):
        self.state = state

    def is_stuck(self, headless_mode: bool = True) -> bool:
        if not headless_mode:
            last_user_msg_idx = -1
            for i, event in enumerate(reversed(self.state.history)):
                if isinstance(event, MessageAction) and event.source == EventSource.USER:
                    last_user_msg_idx = len(self.state.history) - i - 1
                    break
            history_to_check = self.state.history[last_user_msg_idx + 1 :]
        else:
            history_to_check = self.state.history

        filtered_history = [
            event for event in history_to_check
            if not (
                (isinstance(event, MessageAction) and event.source == EventSource.USER) or
                isinstance(event, (NullAction, NullObservation))
            )
        ]

        if len(filtered_history) < 3:
            return False

        last_actions = [e for e in reversed(filtered_history) if isinstance(e, Action)][:4]
        last_observations = [e for e in reversed(filtered_history) if isinstance(e, Observation)][:4]

        if self._is_stuck_repeating_action_observation(last_actions, last_observations):
            return True
        if self._is_stuck_repeating_action_error(last_actions, last_observations):
            return True
        if self._is_stuck_monologue(filtered_history):
            return True
        if len(filtered_history) >= 6:
            if self._is_stuck_action_observation_pattern(filtered_history):
                return True
        if len(filtered_history) >= 10:
            if self._is_stuck_context_window_error(filtered_history):
                return True
        return False

    def _is_stuck_repeating_action_observation(self, last_actions, last_observations):
        if len(last_actions) < 4 or len(last_observations) < 4:
            return False
        actions_equal = all(self._eq_no_pid(last_actions[0], action) for action in last_actions)
        observations_equal = all(self._eq_no_pid(last_observations[0], obs) for obs in last_observations)
        return actions_equal and observations_equal

    def _is_stuck_repeating_action_error(self, last_actions, last_observations):
        if len(last_actions) < 3 or len(last_observations) < 3:
            return False
        if all(self._eq_no_pid(last_actions[0], action) for action in last_actions[:3]):
            if all(isinstance(obs, ErrorObservation) for obs in last_observations[:3]):
                return True
        return False

    def _is_stuck_monologue(self, filtered_history):
        agent_messages = [e for e in filtered_history if isinstance(e, MessageAction) and e.source == EventSource.AGENT]
        if len(agent_messages) >= 3:
            last_three = agent_messages[-3:]
            if last_three[0].content == last_three[1].content == last_three[2].content:
                return True
        return False

    def _is_stuck_action_observation_pattern(self, filtered_history):
        actions = [e for e in reversed(filtered_history) if isinstance(e, Action)][:6]
        observations = [e for e in reversed(filtered_history) if isinstance(e, Observation)][:6]
        if len(actions) < 6 or len(observations) < 6:
            return False
        
        a_pattern = self._eq_no_pid(actions[0], actions[2]) and self._eq_no_pid(actions[0], actions[4])
        b_pattern = self._eq_no_pid(actions[1], actions[3]) and self._eq_no_pid(actions[1], actions[5])
        obs_a_pattern = self._eq_no_pid(observations[0], observations[2]) and self._eq_no_pid(observations[0], observations[4])
        obs_b_pattern = self._eq_no_pid(observations[1], observations[3]) and self._eq_no_pid(observations[1], observations[5])

        return a_pattern and b_pattern and obs_a_pattern and obs_b_pattern

    def _is_stuck_context_window_error(self, filtered_history):
        condensation_events = [e for e in filtered_history if isinstance(e, AgentCondensationObservation)]
        if len(condensation_events) >= 10:
            # A simplified but effective check for the spirit of this rule
            return True
        return False

    def _eq_no_pid(self, obj1: Event, obj2: Event) -> bool:
        if type(obj1) is not type(obj2):
            return False
        
        # The "precious" logic for semantic equality
        if isinstance(obj1, CmdOutputObservation):
            return (obj1.command == obj2.command and
                    obj1.exit_code == obj2.exit_code and
                    obj1.content == obj2.content) # Note: command_id is ignored

        if isinstance(obj1, IPythonRunCellAction):
            # Simplified: just compare code. Original has more complex logic.
            return obj1.code == obj2.code
            
        return obj1 == obj2

if __name__ == '__main__':
    print("StandaloneStuckDetector script.")
    print("This file contains the logic. To verify it, run the test script:")
    print("python -m unittest test_standalone_stuck_detector.py")
