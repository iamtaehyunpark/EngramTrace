from fastapi import APIRouter, Request
from api.deps import brain

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: Request):
    """Binds directly to Brain's Ecphory and Consolidation loop mapping outputs seamlessly to JSON."""
    body = await request.json()
    query = body.get("query", "")
    threshold = body.get("threshold", None)
    semantic_threshold = body.get("semantic_threshold", None)
    no_search = body.get("no_search", False)
    
    if threshold is not None:
        try:
            threshold = float(threshold)
        except ValueError:
            threshold = None
            
    if semantic_threshold is not None:
        try:
            semantic_threshold = float(semantic_threshold)
        except ValueError:
            semantic_threshold = None
            
    if not query:
        return {"response": "Error: Empty query."}
        
    try:
        response = brain.run_inference(query, stage_threshold=threshold, search_threshold=semantic_threshold, no_search=no_search)
        return {"response": response}
    except Exception as e:
        return {"response": f"Runtime Exception: {str(e)}"}
