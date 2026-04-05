import os
import sys
from fastapi import FastAPI, Request
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

sys.path.append(os.path.dirname(__file__))

from src.core.memory import MemoryManager
from src.core.brain import Brain
from src.llm.langchain_client import LangChainClient

import io

class LogCapture(io.StringIO):
    def __init__(self):
        super().__init__()
        self.logs = []
        self.original_stdout = sys.stdout

    def write(self, text):
        # Prevent completely blank whitespace pings
        if text.strip():
            self.logs.append(text.strip())
        self.original_stdout.write(text)

    def flush(self):
        self.original_stdout.flush()

# Globally lock outputs securely through the active array trace dynamically!
log_capture = LogCapture()
sys.stdout = log_capture

app = FastAPI(title="EngramTrace API Core")

# Enable CORS for external frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow UI on any local port to hit API
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Global Engine Initialization
print("BOOTING EXTRACTED ENGRAMTRACE KNOWLEDGE GRAPH ENGINE...")
kb_path = "src/memory/knowledge_base.html"
p_embeddings_path = "src/memory/p_embeddings.json"

print("Starting LLM Models...")
llm = LangChainClient()

print("Hydrating Matrix Indexes...")
memory = MemoryManager(kb_path=kb_path, p_embeddings_path=p_embeddings_path)

print("Synchronizing Drift Hooks...")
brain = Brain(memory_manager=memory, llm_client=llm)


@app.get("/logs")
async def read_logs():
    """Serves the captured system.stdout arrays precisely sequentially to standard polling clients."""
    return {"logs": log_capture.logs}

@app.delete("/logs")
async def clear_logs():
    """Gracefully resets the global tracker array immediately upon new initialization queries!"""
    log_capture.logs = []
    return {"status": "cleared"}

@app.post("/chat")
async def chat_endpoint(request: Request):
    """Binds directly to Brain's Ecphory and Consolidation loop mapping outputs seamlessly to JSON."""
    body = await request.json()
    query = body.get("query", "")
    
    if not query:
        return {"response": "Error: Empty query."}
        
    try:
        response = brain.run_inference(query)
        return {"response": response}
    except Exception as e:
        return {"response": f"Runtime Exception: {str(e)}"}

@app.get("/state")
async def state_endpoint():
    """Formally exposes read-only access scanning current structural memory footprints."""
    try:
        # Provide raw KB string directly from MemoryManager's active beautifulsoup object 
        # (or parse it from the HTML path dynamically ensuring no lock drops happen)
        kb_content = "<empty matrix>"
        if os.path.exists(brain.memory.kb_path):
            with open(brain.memory.kb_path, "r", encoding='utf-8') as f:
                kb_content = f.read()
                
        # Parse running JSON structures tracking immediate logs
        stage_log = []
        log_path = "src/memory/current_stage_log.json"
        import json
        if os.path.exists(log_path):
            with open(log_path, "r", encoding='utf-8') as f:
                try:
                    stage_log = json.load(f)
                except ValueError:
                    stage_log = []
                    
        session_log = []
        session_path = "src/memory/session_log.json"
        if os.path.exists(session_path):
            with open(session_path, "r", encoding='utf-8') as f:
                try:
                    session_log = json.load(f)
                except ValueError:
                    session_log = []

        # Return JSON payload dynamically reflecting immediate system configurations
        return {
            "knowledge_base": kb_content,
            "stage_log": stage_log,
            "session_log": session_log,
            "engram_trace": brain.engram_trace.current_trace
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("Initiating Headless Router at http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
