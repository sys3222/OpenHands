# openhands/graphs/builder.py
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from openhands.graphs.state import GraphState
from openhands.graphs.nodes import agent_think, execute_action, replay_step
from openhands.graphs.schemas import (
    CmdRunAction, CmdOutputObservation, AgentFinishAction, NullObservation,
    AgentDelegateAction, AgentDelegateObservation
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
    
    # In a real system, this would be a more sophisticated registry
    graph_registry = {
        "code_checker": build_code_checker_graph()
    }
    
    sub_graph = graph_registry[action.agent_name]
    sub_graph_result = sub_graph.invoke(action.inputs)
    
    observation = AgentDelegateObservation(outputs=sub_graph_result)
    print(f"Delegation Result: {observation}")
    
    return {"history": [action, observation]}

# =================================================================================
# Graph Builder
# =================================================================================
def build_graph():
    """Builds the main agent graph with delegation capabilities."""
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

# =================================================================================
# Test Runner
# =================================================================================
def run_delegation_test():
    """Runs a test to verify the delegation functionality."""
    print("\n---STARTING DELEGATION TEST---")
    graph = build_graph()

    initial_state = {"history": [], "is_replay": False}
    config = {"configurable": {"thread_id": "delegation-test-thread"}}
    
    final_state = None
    for s in graph.stream(initial_state, config, stream_mode="values"):
        print(s)
        print("----")
        final_state = s

    print("---DELEGATION TEST FINISHED---")
    
    assert final_state is not None
    history = final_state['history']
    # Expected history:
    # 0: CmdRunAction
    # 1: CmdOutputObservation
    # 2: AgentDelegateAction
    # 3: AgentDelegateObservation
    # 4: AgentFinishAction
    # 5: NullObservation
    assert len(history) == 6
    assert isinstance(history[2], AgentDelegateAction)
    assert isinstance(history[3], AgentDelegateObservation)
    assert "OK" in history[3].outputs['result']
    print("Assertion successful: Graph correctly delegated a task and processed the result.")

if __name__ == '__main__':
    run_delegation_test()
