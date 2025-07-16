# cli_client.py
import requests
import json
import argparse

def parse_sse_event(line: str) -> tuple[str | None, str | None]:
    """Parses a single line of an SSE event."""
    if line.startswith('event:'):
        return 'event', line.split(':', 1)[1].strip()
    if line.startswith('data:'):
        return 'data', line.split(':', 1)[1].strip()
    return None, None

def run_graph_session(user_message: str, server_url: str = "http://127.0.0.1:3000"):
    """
    Connects to the server and manually parses the SSE stream.
    """
    endpoint = f"{server_url}/v2/conversations"
    
    try:
        print(f"▶️  Connecting to {endpoint}...")
        response = requests.post(
            endpoint,
            json={"user_message": user_message},
            stream=True
        )
        response.raise_for_status()
        print("✅ Connection successful. Streaming state changes:\n")

        current_event = {}
        for line_bytes in response.iter_lines():
            if not line_bytes:
                # An empty line signifies the end of an event
                if 'data' in current_event:
                    event_type = current_event.get('event', 'message') # Default to 'message' if no event type
                    data = current_event['data']
                    
                    if event_type == 'error':
                        error_data = json.loads(data)
                        print("❌ An error occurred on the server:")
                        print(json.dumps(error_data, indent=2))
                        break
                    
                    if event_type == 'graph_state':
                        update_chunk = json.loads(data)
                        node_name = list(update_chunk.keys())[0]
                        node_output = update_chunk[node_name]
                        
                        print(f"🔄 Executed Node: [ {node_name.upper()} ]")
                        print(json.dumps(node_output, indent=2))
                        print("-" * 40)

                current_event = {} # Reset for the next event
            else:
                line = line_bytes.decode('utf-8')
                key, value = parse_sse_event(line)
                if key:
                    current_event[key] = value

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command-line client for the OpenHands LangGraph engine.")
    parser.add_argument("message", type=str, help="The initial user message.")
    parser.add_argument("--url", type=str, default="http://127.0.0.1:3000", help="Server URL.")
    args = parser.parse_args()
    run_graph_session(args.message, args.url)
