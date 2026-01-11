"""
TrueShift - Vision Service

Handles logic for V-JEPA integration:
1. Registry: Keeps track of the active Colab/GPU node URL.
2. Proxy: Forwards video chunks to the active node for analysis.
"""

import logging
from typing import Optional, Dict, Any
import httpx
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)

class VisionService:
    # In-memory registry for the active Colab URL
    # In production, use Redis to share state across workers.
    _active_node_url: Optional[str] = None
    _node_secret: Optional[str] = None

    @classmethod
    def register_node(cls, url: str) -> str:
        """
        Registers a new active inference node.
        Called by the Colab script on startup.
        """
        if not url.startswith("http"):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        cls._active_node_url = url.rstrip("/")
        logger.info(f"Registered new Vision Node: {cls._active_node_url}")
        return cls._active_node_url

    @classmethod
    def get_active_node(cls) -> str:
        """
        Returns the current active node URL.
        Raises 503 if no node is registered.
        """
        if not cls._active_node_url:
            raise HTTPException(
                status_code=503, 
                detail="Vision Service Unavailable. No active inference node registered."
            )
        return cls._active_node_url

    @classmethod
    async def process_chunk(
        cls, 
        user_id: str, 
        file: UploadFile, 
        session_id: str, 
        chunk_index: int
    ) -> Dict[str, Any]:
        """
        Forwards a video chunk to the Colab node for immediate analysis.
        """
        node_url = cls.get_active_node()
        endpoint = f"{node_url}/predict_chunk"
        
        logger.info(f"Forwarding chunk {chunk_index} for session {session_id} to {endpoint}")

        try:
            # stream the file content to the colab node
            # We read into memory for simplicity, assuming chunks are small (<2MB)
            content = await file.read()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                files = {"file": (file.filename, content, file.content_type)}
                data = {
                    "user_id": user_id, 
                    "session_id": session_id,
                    "chunk_index": chunk_index
                }
                
                response = await client.post(endpoint, files=files, data=data)
                
                if response.status_code != 200:
                    logger.error(f"Colab node error: {response.text}")
                    raise HTTPException(status_code=502, detail="Inference Node Error")
                
                result = response.json()
                
                # Integrations AI Coach
                # V-JEPA node is expected to return 'data' with metrics
                if "data" in result:
                     from app.services.ai_coach_service import ai_coach_service
                     metrics = result["data"]
                     feedback = await ai_coach_service.generate_feedback(metrics)
                     result["data"]["coach_feedback"] = feedback
                
                return result

        except httpx.RequestError as e:
            logger.error(f"Failed to connect to Vision Node: {e}")
            raise HTTPException(status_code=503, detail="Failed to connect to Inference Node")

vision_service = VisionService()
