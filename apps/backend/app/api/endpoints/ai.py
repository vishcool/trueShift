"""
TrueShift - AI API Endpoints

Endpoints for interacting with the AI engine.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.ai.orchestrator import ai_orchestrator
from app.ai.llm_service import gemini_service
# from app.api.deps import get_current_user # Assuming auth dep exists or we skip for now

router = APIRouter()

class ChatRequest(BaseModel):
    user_id: str
    message: str
    context: Optional[Dict[str, Any]] = None

class OrchestrateRequest(BaseModel):
    user_id: str
    mode: str = "full" # full, coaching, workout

@router.post("/chat")
async def chat_with_ai(request: ChatRequest):
    """
    Direct chat endpoint for testing Gemini integration.
    This implements the 'sample flow' requested.
    """
    try:
        # Simple prompt wrapper
        prompt = f"User asks: {request.message}"
        response = await gemini_service.generate_content(
            prompt=prompt,
            system_instruction="You are a helpful assistant for TrueShift."
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orchestrate")
async def run_orchestrator(request: OrchestrateRequest):
    """
    Trigger the full AI agent pipeline.
    """
    try:
        # In a real app, we'd fetch UserState from DB here using request.user_id
        # For now, we'll mock it or pass empty
        from app.models.user_state import UserState
        mock_state = UserState(user_id=request.user_id) # Empty state
        
        result = await ai_orchestrator.process_full_pipeline(
            user_id=request.user_id,
            user_state=mock_state, # We need to handle this properly in real impl
            additional_context={"mode": request.mode}
        )
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
