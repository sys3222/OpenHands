# openhands/graphs/builder.py
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from openhands.graphs.state import GraphState
from openhands.graphs.nodes import agent_think, execute_action, replay_step
from openhands.graphs.schemas import (
    AgentFinishAction, AgentDelegateAction
)
from openhands.graphs.stuck_detector_logic import GraphStuckDetector

# =================================================================================
# Sub-Graph for Delegation
# =================================================================================
def build_code_checker_graph():
    """Builds a simple graph that simulates a code-checking agent."""
    def check_code(state: Dict[str, Any]) -> Dict[str, Any]:
        print("---SUB-GRAPH: Checking Code---")
        code = state.get("code", "")
        if "print" in code:
            return {"result": "Code contains print statements. OK."}
        return {"result": "Code does not contain print statements. FAILED."}

    workflow = StateGraph(Dict[str, Any])
    workflow.add_node("check_code", check_code)
    workflow.set_entry_point("check_code")
    workflow.set_finish_point("check_code")
    return workflow.compile()

# =================================================================================
# Main Graph Nodes & Edges
# =================================================================================
def handle_stuck_error(state: GraphState) -> dict:
    """A node to handle the stuck error, ending the graph."""
    print("---STUCK ERROR HANDLER---")
    return {"error": "Agent is stuck in a loop."}

def handle_delegation(state: GraphState) -> dict:
    """A node that invokes a sub-graph to handle a delegated task."""
    print("---HANDLING DELEGATION---")
    action = state['latest_action']
    
    graph_registry = {
        "code_checker": build_code_checker_graph()
    }
    
    sub_graph = graph_registry[action.agent_name]
    sub_graph_result = sub_graph.invoke(action.inputs)
    
    from openhands.graphs.schemas import AgentDelegateObservation
    observation = AgentDelegateObservation(outputs=sub_graph_result)
    print(f"Delegation Result: {observation}")
    
    return {"history": [action, observation]}

# =================================================================================
# Graph Builder
# =================================================================================
def build_graph():
    """Builds the main agent graph with all capabilities."""
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("agent_think", agent_think)
    workflow.add_node("execute_action", execute_action)
    workflow.add_node("replay_step", replay_step)
    workflow.add_node("handle_delegation", handle_delegation)
    workflow.add_node("handle_stuck_error", handle_stuck_error)

    # Define entry point
    workflow.set_conditional_entry_point(
        lambda state: "replay_step" if state.get("is_replay") else "agent_think",
        {"replay_step": "replay_step", "agent_think": "agent_think"}
    )

    # Define routing logic
    def route_after_think(state: GraphState) -> str:
        if isinstance(state['latest_action'], AgentFinishAction):
            return "finish"
        if isinstance(state['latest_action'], AgentDelegateAction):
            return "handle_delegation"
        return "execute_action"

    workflow.add_conditional_edges("agent_think", route_after_think, {
        "execute_action": "execute_action",
        "handle_delegation": "handle_delegation",
        "finish": END
    })
    
    workflow.add_conditional_edges("replay_step", route_after_think, {
        "execute_action": "execute_action",
        "handle_delegation": "handle_delegation",
        "finish": END
    })

    def route_after_execution(state: GraphState) -> str:
        if GraphStuckDetector(state['history']).is_stuck():
            return "error_stuck"
        return "agent_think"

    workflow.add_conditional_edges("execute_action", route_after_execution, {
        "agent_think": "agent_think",
        "error_stuck": "handle_stuck_error"
    })
    
    workflow.add_edge("handle_delegation", "agent_think")
    workflow.add_edge("handle_stuck_error", END)

    return workflow.compile(checkpointer=MemorySaver())
