import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Load .env
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                try:
                    key, val = line.strip().split("=", 1)
                    os.environ[key.strip()] = val.strip().strip("'\"")
                except ValueError:
                    continue

# Ensure backend root is on Python path so `api` and `src` resolve properly
sys.path.append(os.path.dirname(__file__))

app = FastAPI(title="EngramTrace API Core")

# Enable CORS for external frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow UI on any local port to hit API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Delayed import of routers so sys.path is already updated
from api.routes import chat, system, memory

app.include_router(chat.router)
app.include_router(system.router)
app.include_router(memory.router)

if __name__ == "__main__":
    print("Initiating Headless Router at http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
