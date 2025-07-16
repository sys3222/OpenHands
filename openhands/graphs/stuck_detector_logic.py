# openhands/graphs/stuck_detector_logic.py
from openhands.graphs.schemas import Action, Observation, MessageAction, Event, EventSource, CmdOutputObservation, IPythonRunCellAction, ErrorObservation, AgentCondensationObservation, NullAction, NullObservation

class GraphStuckDetector:
    """
    This class encapsulates the logic for detecting if the agent is stuck in a loop.
    It is adapted from the verified standalone script to work with the GraphState.
    """
    def __init__(self, history: list[Event]):
        self.history = history

    def is_stuck(self, headless_mode: bool = True) -> bool:
        if not headless_mode:
            last_user_msg_idx = -1
            for i, event in enumerate(reversed(self.history)):
                if isinstance(event, MessageAction) and event.source == EventSource.USER:
                    last_user_msg_idx = len(self.history) - i - 1
                    break
            history_to_check = self.history[last_user_msg_idx + 1 :]
        else:
            history_to_check = self.history

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
            print("INFO: Detected stuck condition: Repeating Action/Observation")
            return True
        if self._is_stuck_repeating_action_error(last_actions, last_observations):
            print("INFO: Detected stuck condition: Repeating Action/Error")
            return True
        # Add other checks here in the future
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

    def _eq_no_pid(self, obj1: Event, obj2: Event) -> bool:
        if type(obj1) is not type(obj2):
            return False
        if isinstance(obj1, CmdOutputObservation):
            return (obj1.command == obj2.command and
                    obj1.exit_code == obj2.exit_code and
                    obj1.content == obj2.content)
        if isinstance(obj1, IPythonRunCellAction):
            return obj1.code == obj2.code
        return obj1 == obj2
