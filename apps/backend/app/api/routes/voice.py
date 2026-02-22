"""
TrueShift - Voice Routes

Real-time WebSocket endpoints for conversational AI coaching.
"""

import logging
import json
import base64
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.services.user_state_engine import UserStateEngine
from app.services.voice_agent_service import voice_agent_service
from app.services.agent_memory_service import agent_memory_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{user_id}")
async def voice_websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket for real-time STT and agents.
    Accepts: Binary frames (PCM 16000Hz base64 encoded) or JSON control signals.
    Emits: JSON describing state, transcript, or base64 TTS audio.
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for user {user_id}")

    try:
        # Get async DB session
        # Note: Depending on dependency injection with WebSockets, we manage session manually here
        from app.core.database import async_session_factory
        
        async with async_session_factory() as db:
            # Check user
            stmt = select(User).where(User.firebase_uid == user_id)
            result = await db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                await websocket.send_json({"type": "error", "message": "User not found"})
                await websocket.close(1008)
                return

            # Fetch context for agent routing later
            state_engine = UserStateEngine(db)
            user_state = await state_engine.get_or_create_state(user_id)

            await websocket.send_json({"type": "status", "message": "Connected to Voice Coach"})

            buffer = []
            sarvam_client = voice_agent_service.sarvam_client
            
            while True:
                # We expect JSON objects (if control) or raw text (base64 audio chunk)
                # Clients will send JSON like {"type": "audio", "data": "base64..."}
                # or {"type": "stop"} indicating end of speech.
                message = await websocket.receive_text()
                
                try:
                    data = json.loads(message)
                except json.JSONDecodeError:
                    continue
                    
                msg_type = data.get("type")
                
                if msg_type == "audio":
                    b64_audio = data.get("data")
                    if b64_audio:
                        buffer.append(b64_audio)
                
                elif msg_type == "stop":
                    if not buffer:
                        logger.warning("Stop signal received but no audio buffer exists.")
                        await websocket.send_json({"type": "status", "message": "No audio received"})
                        continue
                        
                    logger.info(f"Received stop signal. Buffer contains {len(buffer)} audio chunks.")
                    await websocket.send_json({"type": "state", "status": "processing"})
                    
                    # 1. Process STT directly bridging base64 buffer to Sarvam Streaming API
                    transcript = ""
                    logger.info("Opening Sarvam STT stream...")
                    try:
                        async with sarvam_client.speech_to_text_streaming.connect(
                            model="saaras:v3",
                            mode="transcribe",
                            language_code="en-IN",
                            high_vad_sensitivity=False,
                            flush_signal=True
                        ) as ws_stt:
                            # Send all chunks
                            # STT needs base64 string
                            merged_audio = "".join(buffer) 
                            logger.info(f"Sending {len(merged_audio)} bytes of base64 audio to Sarvam...")
                            
                            # Transcribe
                            await ws_stt.transcribe(
                                audio=merged_audio,
                                encoding="audio/wav",
                                sample_rate=16000
                            )
                            # Force processing
                            await ws_stt.flush()
                            logger.info("Sent flush signal to Sarvam, awaiting response...")
                            
                            stt_response = await ws_stt.recv() # Gets first full transcript message
                            logger.info(f"Received raw STT response from Sarvam: {stt_response}")
                            
                            # Parse JSON if response is raw string
                            if isinstance(stt_response, str):
                                try:
                                    res_dict = json.loads(stt_response)
                                    if "text" in res_dict:
                                        transcript = res_dict["text"]
                                    else:
                                        transcript = stt_response
                                except json.JSONDecodeError:
                                    transcript = stt_response
                                    
                    except Exception as e:
                        logger.error(f"STT Error: {e}")
                        await websocket.send_json({"type": "error", "message": "Transcription failed."})
                        buffer.clear()
                        continue
                        
                    # Clean the buffer for next interaction
                    buffer.clear()
                    
                    if not transcript or len(transcript) < 2:
                        logger.warning("Transcript was empty or too short. Ignoring.")
                        await websocket.send_json({"type": "state", "status": "idle"})
                        continue
                        
                    logger.info(f"Final parsed transcript: '{transcript}'")
                    # Stream the transcript down to client
                    await websocket.send_json({"type": "transcript", "text": transcript})
                    
                    # 2. Add to logs
                    await agent_memory_service.save_conversation(db, user_id, "user", transcript)
                    
                    # 3. Route to Multi-Agent ADK Layer
                    logger.info("Routing transcript to Agent system...")
                    agent_reply = await voice_agent_service.get_agent_response(user_id, transcript, user_state)
                    logger.info(f"Agent system replied: '{agent_reply}'")
                    
                    # Save assistant reply
                    await agent_memory_service.save_conversation(db, user_id, "model", agent_reply, agent_name="VoiceRouter")
                    
                    # Send text response back to screen
                    await websocket.send_json({"type": "agent_text", "text": agent_reply})
                    
                    # 4. Generate TTS via Sarvam
                    logger.info("Generating TTS via Sarvam...")
                    await websocket.send_json({"type": "state", "status": "speaking"})
                    audio_b64 = await voice_agent_service.generate_tts(agent_reply)
                    
                    if audio_b64:
                        logger.info(f"TTS generated successfully ({len(audio_b64)} bytes base64). Sending to client.")
                        await websocket.send_json({"type": "audio_out", "data": audio_b64})
                    else:
                        logger.error("TTS generation failed (returned None).")
                        await websocket.send_json({"type": "error", "message": "Failed to generate speech."})
                        
                    await websocket.send_json({"type": "state", "status": "idle"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket unhandled error: {e}", exc_info=True)
        try:
            await websocket.close(1011)
        except:
            pass
