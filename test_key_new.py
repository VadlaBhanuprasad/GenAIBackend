import requests
import os
from dotenv import load_dotenv

load_dotenv(override=True)

key = os.getenv("OPEN_ROUTER_KEY")
url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}
payload = {
    "model": "stepfun/step-3.5-flash:free",
    "messages": [{"role": "user", "content": "Tell me a joke"}]
}

print(f"Testing with key: {key[:5]}...{key[-5:] if key else 'None'} (len: {len(key) if key else 0})")
resp = requests.post(url, headers=headers, json=payload)
print(f"Status Code: {resp.status_code}")
print(f"Response: {resp.text}")
