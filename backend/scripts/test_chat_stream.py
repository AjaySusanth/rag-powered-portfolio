import httpx
import json

url = "http://127.0.0.1:8000/chat"
payload = {
    "message": "Tell me about the talentforge project",
    "session_id": "demo-session"
}

print(f"Connecting to {url}...")
try:
    with httpx.stream("POST", url, json=payload, timeout=60.0) as r:
        if r.status_code != 200:
            print(f"Failed with status code: {r.status_code}")
            print(r.read().decode())
        else:
            for line in r.iter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    data_str = line[len("data: "):]
                    if data_str == "[DONE]":
                        print("\n[DONE]")
                        break
                    try:
                        event = json.loads(data_str)
                        if event.get("event") == "token":
                            print(event.get("token"), end="", flush=True)
                        elif event.get("event") == "error":
                            print(f"\n[Error: {event.get('message')}]")
                    except json.JSONDecodeError:
                        print(f"\n[Raw data: {data_str}]")
except Exception as e:
    print(f"\nAn error occurred: {e}")
