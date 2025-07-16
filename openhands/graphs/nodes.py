# openhands/graphs/nodes.py
import random
from openhands.graphs.state import GraphState
from openhands.graphs.schemas import (
    Action, CmdRunAction, AgentFinishAction, CmdOutputObservation, 
    Observation, NullObservation, AgentDelegateAction
)
from openhands.graphs.synchronous_runtime import SyncRuntime

# This is now a global instance for the graph to use.
# In a more complex app, this would be managed and passed around.
RUNTIME = SyncRuntime()

def agent_think(state: GraphState) -> dict:
    """
    Simulates the agent's thinking process. It can decide to continue, delegate, or finish.
    """
    print("---AGENT THINKING---")
    
    if len(state['history']) == 2:
        action = AgentDelegateAction(
            agent_name="code_checker",
            inputs={"code": "print('hello world')"}
        )
    elif len(state['history']) > 4:
        action = AgentFinishAction()
    else:
        # Use a real command that will work
        action = CmdRunAction(command="echo 'Hello from the runtime!'")
    
    print(f"Action: {action}")
    return {"latest_action": action}

def execute_action(state: GraphState) -> dict:
    """
    Executes the action using the real runtime and adds the [action, observation] pair to history.
    """
    print("---EXECUTING ACTION---")
    action = state['latest_action']
    
    # Use the synchronous runtime to execute the action
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