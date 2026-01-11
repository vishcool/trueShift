"""
TrueShift - Vision API

Endpoints for Video Analysis logic.
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl

from app.services.vision_service import vision_service
# form app.api.deps import get_current_user # Uncomment when auth is ready
from app.core.config import settings

router = APIRouter()

class RegisterNodeRequest(BaseModel):
    url: HttpUrl
    secret: str

class AnalysisResponse(BaseModel):
    status: str
    data: dict # Includes 'coach_feedback' injected by AICoachService

@router.post("/internal/register", status_code=status.HTTP_200_OK)
async def register_vision_node(payload: RegisterNodeRequest):
    """
    Internal endpoint called by the Colab instance to register its URL.
    Protected by a simple shared secret check.
    """
    # Simple security check
    # In production, use proper service-to-service auth
    if payload.secret != settings.secret_key:
         raise HTTPException(status_code=403, detail="Invalid secret")

    vision_service.register_node(str(payload.url))
    return {"message": "Node registered successfully"}

@router.post("/analyze-chunk", response_model=AnalysisResponse)
async def analyze_video_chunk(
    file: UploadFile = File(...),
    session_id: str = Form(...),
    chunk_index: int = Form(...),
    # current_user = Depends(get_current_user) # Uncomment when auth is ready
):
    """
    Receives a video chunk from the mobile app and forwards it to the V-JEPA model.
    """
    # For now, mocking user_id until auth is fully integrated in this context
    user_id = "test-user-id" 
    
    result = await vision_service.process_chunk(
        user_id=user_id,
        file=file,
        session_id=session_id,
        chunk_index=chunk_index
    )
    
    return AnalysisResponse(status="success", data=result)
