# cli_client.py
import requests
import json
import argparse
import sseclient

def run_graph_session(user_message: str, server_url: str = "http://127.0.0.1:3000"):
    """
    Connects to the OpenHands server's V2 endpoint and streams the graph state.
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
        
        # Pass the response object directly to the SSEClient
        client = sseclient.SSEClient(response)
        
        print("✅ Connection successful. Streaming state changes:\n")
        
        for event in client.events():
            if event.event == 'error':
                print(f"❌ Server-side Error: {event.data}")
                break
            
            if event.event == 'graph_state':
                update_chunk = json.loads(event.data)
                
                node_name = list(update_chunk.keys())[0]
                node_output = update_chunk[node_name]
                
                if node_output and node_output.get('error'):
                    print(f"🛑 Node [ {node_name.upper()} ] reported an error:")
                    print(json.dumps(node_output, indent=2))
                else:
                    print(f"🔄 Executed Node: [ {node_name.upper()} ]")
                    print(json.dumps(node_output, indent=2))
                
                print("-" * 40)

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection Error: Could not connect to the server at {server_url}.")
        print(f"   Please ensure the OpenHands server is running.")
        print(f"   Error details: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command-line client for the OpenHands LangGraph engine.")
    parser.add_argument(
        "message",
        type=str,
        help="The initial user message to start the agent session."
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://127.0.0.1:3000",
        help="The URL of the OpenHands server."
    )
    
    args = parser.parse_args()
    
    run_graph_session(args.message, args.url)
