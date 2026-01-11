"""
TrueShift - AI API Endpoints

Endpoints for interacting with the AI engine.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
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
async def chat_with_ai(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Direct chat endpoint with persistence.
    Saves message, hydrates history, runs agent, saves response.
    """
    try:
        # We need a proper UserState to pass to the agent
        # For now, we'll fetch or create a dummy one if not in DB
        from app.models.user_state import UserState
        # In real impl, we'd fetch this from DB using request.user_id
        mock_state = UserState(user_id=request.user_id) 
        
        response = await ai_orchestrator.process_chat_message(
            db=db,
            user_id=request.user_id,
            message=request.message,
            user_state=mock_state
        )
        
        return {
            "response": response.content,
            "agent": response.agent_name,
            "confidence": response.confidence
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/orchestrate")
async def run_orchestrator(request: OrchestrateRequest):
    """
    Trigger the full AI agent pipeline.
    """
    try:
        from app.models.user_state import UserState
        mock_state = UserState(user_id=request.user_id) # Empty state
        
        result = await ai_orchestrator.process_full_pipeline(
            user_id=request.user_id,
            user_state=mock_state, 
            additional_context={"mode": request.mode}
        )
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
