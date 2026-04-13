import os
import json
from fastapi import APIRouter
from api.deps import log_capture, brain

router = APIRouter()

@router.get("/logs")
async def read_logs():
    """Serves the captured system.stdout arrays precisely sequentially to standard polling clients."""
    return {"logs": log_capture.logs}

@router.delete("/logs")
async def clear_logs():
    """Gracefully resets the global tracker array immediately upon new initialization queries!"""
    log_capture.logs = []
    return {"status": "cleared"}

@router.post("/day-change")
async def force_day_change():
    """Forces an immediate atomization of the Knowledge Base and resets the Day Stage cycle natively."""
    try:
        stage_log = brain.engram_trace._get_stage_log()
        if len(stage_log) > 0:
            brain.consolidate_and_transition()
        brain.memory.atomizer(brain.llm, compress=True)
        brain.engram_trace.start_new_stage()
        return {"status": "success", "message": "Day change forced successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/state")
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
        if os.path.exists(brain.engram_trace.stage_log_path):
            with open(brain.engram_trace.stage_log_path, "r", encoding='utf-8') as f:
                try:
                    stage_log = json.load(f)
                except ValueError:
                    stage_log = []
                    
        session_log = []
        if os.path.exists(brain.engram_trace.session_log_path):
            with open(brain.engram_trace.session_log_path, "r", encoding='utf-8') as f:
                try:
                    session_log = json.load(f)
                except ValueError:
                    session_log = []

        # Return JSON payload dynamically reflecting immediate system configurations
        return {
            "knowledge_base": kb_content,
            "stage_log": stage_log,
            "session_log": session_log,
            "engram_trace": list(brain.engram_trace.current_trace)
        }
    except Exception as e:
        return {"error": str(e)}
