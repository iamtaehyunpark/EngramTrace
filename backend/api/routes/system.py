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

@router.get("/sessions")
async def list_sessions():
    """Lists all available sessions and the currently active one."""
    sessions_dir = "src/memory/sessions"
    os.makedirs(sessions_dir, exist_ok=True)
    sessions = []
    for f in os.listdir(sessions_dir):
        if f.endswith(".json") and not f.endswith("_stage.json"):
            sessions.append(f[:-5])
    return {
        "sessions": sessions,
        "active_session": brain.engram_trace.active_session_id
    }

@router.post("/sessions/{session_id}")
async def select_session(session_id: str):
    """Sets the active session, creating it if it doesn't exist."""
    try:
        brain.engram_trace.set_session(session_id)
        return {"status": "success", "active_session": session_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Deletes a session and its stage log. Switches back to 'default' if active."""
    try:
        import shutil
        sessions_dir = "src/memory/sessions"
        s_file = f"{sessions_dir}/{session_id}.json"
        stage_file = f"{sessions_dir}/{session_id}_stage.json"
        if os.path.exists(s_file): os.remove(s_file)
        if os.path.exists(stage_file): os.remove(stage_file)
        
        if session_id in brain.engram_trace.sessions:
            del brain.engram_trace.sessions[session_id]
            
        if brain.engram_trace.active_session_id == session_id:
            brain.engram_trace.set_session("default")
            
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
