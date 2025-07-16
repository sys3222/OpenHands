# openhands/graphs/nodes.py
import random
from openhands.graphs.state import GraphState
from openhands.graphs.schemas import (
    Action, CmdRunAction, AgentFinishAction, CmdOutputObservation, 
    Observation, NullObservation, AgentDelegateAction
)
from openhands.graphs.synchronous_runtime import SyncRuntime

RUNTIME = SyncRuntime()

def agent_think(state: GraphState) -> dict:
    """
    A more realistic simulation of the agent's thinking process.
    """
    print("---AGENT THINKING---")
    
    history = state.get("history", [])
    
    # Only finish if the last action was a command and it was successful
    if history and isinstance(history[-1], CmdOutputObservation):
        # A more robust check to avoid finishing on stuck loops
        if len(history) > 8:
             action = AgentFinishAction()
        else:
             action = CmdRunAction(command=f"echo 'Thinking after step {len(history)}'")
    else:
        action = CmdRunAction(command=f"echo 'Step {len(history)}'")
    
    print(f"Action: {action}")
    return {"latest_action": action}

def execute_action(state: GraphState) -> dict:
    """
    Executes the action and adds the [action, observation] pair to history.
    """
    print("---EXECUTING ACTION---")
    action = state['latest_action']
    
    if isinstance(action, AgentFinishAction):
        return {"history": [action]}

    observation = RUNTIME.execute(action)
    
    print(f"Observation: {observation}")
    return {"history": [action, observation]}

def replay_step(state: GraphState) -> dict:
    """
    Pops the next action from the replay history and provides it as the next action.
    """
    print("---REPLAYING STEP---")
    replay_actions = state['replay_history']
    next_action = replay_actions.pop(0)
    
    print(f"Replaying Action: {next_action}")
    return {
        "latest_action": next_action,
        "replay_history": replay_actions,
        "is_replay": bool(replay_actions)
    }
