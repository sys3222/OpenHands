# openhands/server/routes/v2_conversation.py
import asyncio
import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from openhands.graphs.builder import build_graph
from openhands.server.dependencies import get_dependencies

# This is the new router for our LangGraph-based sessions
v2_app = APIRouter(
    prefix='/v2',
    dependencies=get_dependencies()
)

class V2InitSessionRequest(BaseModel):
    user_message: str

async def graph_event_generator(user_message: str):
    """
    This generator function is the core of our streaming endpoint.
    It invokes the graph and yields each state change as a Server-Sent Event.
    """
    graph = build_graph()
    
    initial_state = {
        "history": [],
        "replay_history": [],
        "is_replay": False,
        "latest_action": None,
        "error": None,
        # We can add the initial user message to the state if needed,
        # but for now, our mock agent_think doesn't use it.
    }
    
    # Each graph execution needs a unique thread_id for checkpoints
    import uuid
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}

    # Use the graph's stream method to get real-time updates
    async for chunk in graph.astream(initial_state, config, stream_mode="values"):
        # The state is the last item in the chunk
        state_key = list(chunk.keys())[-1]
        state_value = chunk[state_key]
        
        # Yield the event as a JSON string
        yield ServerSentEvent(data=json.dumps({state_key: state_value}), event="graph_state")
        await asyncio.sleep(0.1) # Small delay for streaming effect

@v2_app.post("/conversations")
async def new_v2_conversation(req: V2InitSessionRequest):
    """
    Starts a new conversation using the LangGraph engine and streams
    the state changes back to the client.
    """
    return EventSourceResponse(graph_event_generator(req.user_message))
