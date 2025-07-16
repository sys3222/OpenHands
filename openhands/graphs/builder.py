# openhands/graphs/builder.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from openhands.graphs.state import GraphState
from openhands.graphs.nodes import agent_think, execute_action, replay_step
from openhands.graphs.schemas import AgentFinishAction
from openhands.graphs.stuck_detector_logic import GraphStuckDetector

def handle_stuck_error(state: GraphState) -> dict:
    print("---STUCK ERROR HANDLER---")
    return {"error": "Agent is stuck in a loop."}

def build_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("agent_think", agent_think)
    workflow.add_node("execute_action", execute_action)
    workflow.add_node("replay_step", replay_step)
    workflow.add_node("handle_stuck_error", handle_stuck_error)

    def should_start(state: GraphState) -> str:
        if state.get("is_replay"):
            return "replay_step"
        return "agent_think"

    workflow.set_conditional_entry_point(should_start, {
        "replay_step": "replay_step",
        "agent_think": "agent_think",
    })

    workflow.add_edge("agent_think", "execute_action")
    workflow.add_edge("replay_step", "execute_action")

    def decide_after_execution(state: GraphState) -> str:
        if GraphStuckDetector(state['history']).is_stuck():
            return "error_stuck"
        
        # The last event in history is the observation from the action just executed
        last_event = state['history'][-1]
        if isinstance(last_event, AgentFinishAction):
             return "finish"

        if state.get("is_replay"):
            return "replay_step"
            
        return "agent_think"

    workflow.add_conditional_edges("execute_action", decide_after_execution, {
        "replay_step": "replay_step",
        "agent_think": "agent_think",
        "error_stuck": "handle_stuck_error",
        "finish": END,
    })

    workflow.add_edge("handle_stuck_error", END)

    return workflow.compile(checkpointer=MemorySaver())
