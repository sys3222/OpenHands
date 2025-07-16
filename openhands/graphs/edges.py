# openhands/graphs/edges.py
from openhands.graphs.state import GraphState
from openhands.graphs.schemas import AgentFinishAction
from openhands.graphs.stuck_detector_logic import GraphStuckDetector

def decide_next_step(state: GraphState) -> str:
    """
    Determines the next node to execute.
    It prioritizes replay, then checks for stuck conditions, then decides the next step.
    """
    print("---DECIDING NEXT STEP---")

    # 1. Prioritize Replay
    if state.get('is_replay'):
        print("Decision: REPLAY_STEP")
        return "replay_step"

    # 2. Check for Stuck conditions
    detector = GraphStuckDetector(state['history'])
    if detector.is_stuck():
        print("Decision: STUCK")
        return "error_stuck"

    # 3. Normal Logic
    action = state['latest_action']
    if isinstance(action, AgentFinishAction):
        print("Decision: FINISH")
        return "finish"
    else:
        print("Decision: CONTINUE_THINKING")
        return "continue_thinking"