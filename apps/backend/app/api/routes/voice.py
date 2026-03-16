"""
TrueShift - Voice Routes

Real-time WebSocket endpoints for conversational AI coaching and voice preferences.
"""

import json
import logging
from hashlib import sha1
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.conversation import ConversationLog
from app.models.event import EventSource, EventType
from app.models.user import User
from app.services.agent_memory_service import agent_memory_service
from app.services.event_processor import EventPayload, EventProcessor
from app.services.user_state_engine import UserStateEngine
from app.services.voice_agent_service import voice_agent_service

logger = logging.getLogger(__name__)

router = APIRouter()


class VoicePreferencesResponse(BaseModel):
    preferred_language_code: str
    preferred_voice: str
    default_mode: str
    tts_enabled: bool


class VoicePreferencesUpdate(BaseModel):
    preferred_language_code: str | None = None
    preferred_voice: str | None = None
    default_mode: str | None = None
    tts_enabled: bool | None = None


class VoiceSessionSummary(BaseModel):
    session_id: str
    started_at: str
    last_message_at: str
    message_count: int


def _voice_preferences_from_user(user: User) -> dict:
    preferences = dict(user.preferences or {})
    voice = dict(preferences.get("voice_preferences") or {})
    return {
        "preferred_language_code": voice.get("preferred_language_code", "en-IN"),
        "preferred_voice": voice.get("preferred_voice", "meera"),
        "default_mode": voice.get("default_mode", "general"),
        "tts_enabled": bool(voice.get("tts_enabled", True)),
    }


async def _transcribe_audio_buffer(sarvam_client, audio_buffer: list[str], language_code: str) -> str:
    transcript = ""
    if not audio_buffer:
        return transcript

    async with sarvam_client.speech_to_text_streaming.connect(
        model="saaras:v3",
        mode="transcribe",
        language_code=language_code,
        high_vad_sensitivity=False,
        flush_signal=True,
    ) as ws_stt:
        merged_audio = "".join(audio_buffer)
        await ws_stt.transcribe(
            audio=merged_audio,
            encoding="audio/wav",
            sample_rate=16000,
        )
        await ws_stt.flush()

        stt_response = await ws_stt.recv()
        if isinstance(stt_response, str):
            try:
                parsed = json.loads(stt_response)
                transcript = parsed.get("text", stt_response)
            except json.JSONDecodeError:
                transcript = stt_response

    return transcript.strip()


async def _persist_voice_turn_event(
    db: AsyncSession,
    user_id: str,
    session_context: dict,
    transcript: str,
) -> None:
    processor = EventProcessor(db)
    workout_context = session_context.get("workout_context") or {}
    workout_session_id = workout_context.get("session_id")
    transcript_clean = transcript.strip()
    transcript_digest = sha1(transcript_clean.encode("utf-8")).hexdigest()[:16]
    await processor.process(
        user_id=user_id,
        event_payload=EventPayload(
            event_type=EventType.VOICE_TURN_COMPLETED.value,
            payload={
                "mode": session_context.get("mode", "general"),
                "language_code": session_context.get("language_code", "en-IN"),
                "workout_session_id": workout_session_id,
                "transcript_length": len(transcript_clean),
            },
            session_id=session_context.get("session_id"),
            correlation_id=f"voice-turn:{session_context.get('session_id')}:{len(transcript_clean)}:{transcript_digest}",
        ),
        source=EventSource.AI,
    )


async def _persist_voice_workout_update(
    db: AsyncSession,
    user_id: str,
    session_context: dict,
    workout_update: dict,
) -> None:
    if workout_update.get("type") != "log_set":
        return

    processor = EventProcessor(db)
    workout_context = session_context.get("workout_context") or {}
    exercises = workout_context.get("exercises") or []
    exercise_index = int(workout_update.get("exercise_index") or 0)
    exercise_name = ""
    if 0 <= exercise_index < len(exercises):
        exercise_name = str(exercises[exercise_index].get("name", "Exercise"))

    session_id = workout_context.get("session_id") or session_context.get("session_id")
    completed_at = workout_update.get("completed_at")
    correlation_bits = [
        str(session_id or "voice-session"),
        str(exercise_index),
        str(workout_update.get("set_number", "")),
        str(workout_update.get("reps", "")),
        str(workout_update.get("weight", "")),
        str(completed_at or ""),
    ]

    await processor.process(
        user_id=user_id,
        event_payload=EventPayload(
            event_type=EventType.WORKOUT_SET_LOGGED.value,
            payload={
                "exercise_index": exercise_index,
                "exercise_name": exercise_name,
                "set_number": workout_update.get("set_number"),
                "reps": workout_update.get("reps"),
                "weight": workout_update.get("weight"),
                "completed_at": completed_at,
                "source": workout_update.get("source", "voice"),
            },
            session_id=session_id,
            correlation_id=f"voice-set:{':'.join(correlation_bits)}",
        ),
        source=EventSource.AI,
    )


@router.get("/preferences", response_model=VoicePreferencesResponse)
async def get_voice_preferences(current_user: User = Depends(get_current_user)):
    return VoicePreferencesResponse(**_voice_preferences_from_user(current_user))


@router.put("/preferences", response_model=VoicePreferencesResponse)
async def update_voice_preferences(
    payload: VoicePreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current = _voice_preferences_from_user(current_user)
    updates = payload.model_dump(exclude_none=True)
    current.update(updates)

    all_preferences = dict(current_user.preferences or {})
    all_preferences["voice_preferences"] = current
    current_user.preferences = all_preferences

    await db.commit()
    await db.refresh(current_user)

    return VoicePreferencesResponse(**_voice_preferences_from_user(current_user))


@router.get("/sessions", response_model=list[VoiceSessionSummary])
async def get_voice_sessions(
    limit: int = Query(default=20, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConversationLog)
        .where(ConversationLog.user_id == current_user.id)
        .where(ConversationLog.session_id.is_not(None))
        .where(ConversationLog.session_id.like("voice-%"))
        .order_by(desc(ConversationLog.created_at))
        .limit(500)
    )
    rows = result.scalars().all()

    sessions: dict[str, dict] = {}
    for row in rows:
        sid = row.session_id
        if not sid:
            continue
        if sid not in sessions:
            sessions[sid] = {
                "session_id": sid,
                "started_at": row.created_at,
                "last_message_at": row.created_at,
                "message_count": 0,
            }
        sessions[sid]["message_count"] += 1
        sessions[sid]["started_at"] = min(sessions[sid]["started_at"], row.created_at)
        sessions[sid]["last_message_at"] = max(sessions[sid]["last_message_at"], row.created_at)

    summaries = sorted(sessions.values(), key=lambda item: item["last_message_at"], reverse=True)[:limit]

    return [
        VoiceSessionSummary(
            session_id=s["session_id"],
            started_at=s["started_at"].isoformat(),
            last_message_at=s["last_message_at"].isoformat(),
            message_count=s["message_count"],
        )
        for s in summaries
    ]


@router.get("/sessions/{session_id}")
async def get_voice_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ConversationLog)
        .where(ConversationLog.user_id == current_user.id)
        .where(ConversationLog.session_id == session_id)
        .order_by(ConversationLog.created_at.asc())
    )
    logs = result.scalars().all()
    if not logs:
        raise HTTPException(status_code=404, detail="Voice session not found")

    return {
        "session_id": session_id,
        "messages": [
            {
                "id": str(log.id),
                "role": log.role,
                "content": log.content,
                "created_at": log.created_at.isoformat(),
                "agent_name": log.agent_name,
            }
            for log in logs
        ],
    }


@router.websocket("/ws/{user_id}")
async def voice_websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket for streaming STT/TTS.

    Client messages:
    - {"type":"context", "mode":"workout", "language_code":"en-IN", "voice":"meera"}
    - {"type":"start", "session_id":"voice-..."}
    - {"type":"audio_chunk", "data":"base64", "seq":1}
    - {"type":"stop"}

    Server messages:
    - status/state/transcript/agent_text/audio_out/error
    """
    await websocket.accept()
    logger.info("WebSocket connected for user %s", user_id)

    from app.core.database import async_session_factory

    try:
        async with async_session_factory() as db:
            result = await db.execute(select(User).where(User.firebase_uid == user_id))
            user = result.scalar_one_or_none()
            if not user:
                await websocket.send_json({"type": "error", "message": "User not found"})
                await websocket.close(1008)
                return

            internal_user_id = str(user.id)
            state_engine = UserStateEngine(db)
            await state_engine.get_or_create_state(internal_user_id)

            voice_preferences = _voice_preferences_from_user(user)
            voice_session_id = f"voice-{uuid4().hex[:12]}"
            query_tts = websocket.query_params.get("tts_enabled")
            session_context = {
                "mode": websocket.query_params.get("mode", voice_preferences["default_mode"]),
                "language_code": websocket.query_params.get("language_code", voice_preferences["preferred_language_code"]),
                "voice": websocket.query_params.get("voice", voice_preferences["preferred_voice"]),
                "tts_enabled": (query_tts.lower() == "true") if isinstance(query_tts, str) else voice_preferences["tts_enabled"],
                "session_id": websocket.query_params.get("session_id", voice_session_id),
                "partial_transcripts": [],
                "workout_context": None,
            }

            await websocket.send_json(
                {
                    "type": "status",
                    "message": "Connected to Voice Coach",
                    "session_id": session_context["session_id"],
                    "voice_preferences": voice_preferences,
                }
            )

            audio_buffer: list[str] = []
            sarvam_client = voice_agent_service.sarvam_client

            while True:
                raw_message = await websocket.receive_text()

                try:
                    data = json.loads(raw_message)
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("type")

                if msg_type == "context":
                    mode = data.get("mode")
                    language_code = data.get("language_code")
                    voice = data.get("voice")
                    tts_enabled = data.get("tts_enabled")
                    workout_context = data.get("workout_context")

                    if isinstance(mode, str) and mode:
                        session_context["mode"] = mode.strip().lower()
                    if isinstance(language_code, str) and language_code:
                        session_context["language_code"] = language_code
                    if isinstance(voice, str) and voice:
                        session_context["voice"] = voice
                    if isinstance(tts_enabled, bool):
                        session_context["tts_enabled"] = tts_enabled
                    if isinstance(workout_context, dict):
                        session_context["workout_context"] = workout_context
                    continue

                if msg_type == "start":
                    maybe_sid = data.get("session_id")
                    if isinstance(maybe_sid, str) and maybe_sid:
                        session_context["session_id"] = maybe_sid
                    else:
                        session_context["session_id"] = f"voice-{uuid4().hex[:12]}"
                    audio_buffer.clear()
                    session_context["partial_transcripts"] = []
                    processor = EventProcessor(db)
                    await processor.process(
                        user_id=internal_user_id,
                        event_payload=EventPayload(
                            event_type=EventType.VOICE_SESSION_STARTED.value,
                            payload={
                                "mode": session_context.get("mode", "general"),
                                "language_code": session_context.get("language_code", "en-IN"),
                                "tts_enabled": bool(session_context.get("tts_enabled", True)),
                                "workout_session_id": (session_context.get("workout_context") or {}).get("session_id"),
                            },
                            session_id=session_context["session_id"],
                            correlation_id=f"voice-session-start:{session_context['session_id']}",
                        ),
                        source=EventSource.AI,
                    )
                    await websocket.send_json({"type": "state", "status": "idle", "session_id": session_context["session_id"]})
                    continue

                if msg_type in {"audio", "audio_chunk"}:
                    b64_audio = data.get("data")
                    if isinstance(b64_audio, str) and b64_audio:
                        audio_buffer.append(b64_audio)
                    continue

                if msg_type == "process_segment":
                    if not audio_buffer:
                        continue
                    try:
                        transcript_partial = await _transcribe_audio_buffer(
                            sarvam_client,
                            audio_buffer,
                            session_context.get("language_code", "en-IN"),
                        )
                    except Exception as exc:
                        logger.error("Partial STT Error: %s", exc)
                        await websocket.send_json({"type": "error", "message": "Partial transcription failed."})
                        audio_buffer.clear()
                        continue

                    audio_buffer.clear()
                    if transcript_partial:
                        session_context["partial_transcripts"].append(transcript_partial)
                        await websocket.send_json({"type": "transcript_partial", "text": transcript_partial})
                    continue

                if msg_type == "stop":
                    if not audio_buffer and not session_context["partial_transcripts"]:
                        await websocket.send_json({"type": "status", "message": "No audio received"})
                        continue

                    await websocket.send_json({"type": "state", "status": "processing"})

                    transcript = ""
                    try:
                        transcript = await _transcribe_audio_buffer(
                            sarvam_client,
                            audio_buffer,
                            session_context.get("language_code", "en-IN"),
                        )
                    except Exception as exc:
                        logger.error("STT Error: %s", exc)
                        await websocket.send_json({"type": "error", "message": "Transcription failed."})
                        audio_buffer.clear()
                        continue

                    audio_buffer.clear()
                    all_parts = session_context.get("partial_transcripts", [])
                    full_transcript = " ".join([*all_parts, transcript]).strip()
                    session_context["partial_transcripts"] = []

                    if not full_transcript or len(full_transcript.strip()) < 2:
                        await websocket.send_json({"type": "state", "status": "idle"})
                        continue

                    await websocket.send_json({"type": "transcript", "text": full_transcript})

                    await _persist_voice_turn_event(
                        db=db,
                        user_id=internal_user_id,
                        session_context=session_context,
                        transcript=full_transcript,
                    )

                    await agent_memory_service.save_conversation(
                        db,
                        internal_user_id,
                        "user",
                        full_transcript,
                        session_id=session_context["session_id"],
                        agent_name="VoiceRouter",
                    )

                    latest_user_state = await state_engine.get_or_create_state(internal_user_id)
                    agent_result = await voice_agent_service.get_agent_response(
                        internal_user_id,
                        full_transcript,
                        latest_user_state,
                        session_context=session_context,
                    )
                    agent_reply = agent_result.get("text", "I heard you, let's keep working.")
                    workout_update = agent_result.get("workout_update")
                    if isinstance(workout_update, dict):
                        await _persist_voice_workout_update(
                            db=db,
                            user_id=internal_user_id,
                            session_context=session_context,
                            workout_update=workout_update,
                        )
                        session_context["workout_context"] = {
                            **(session_context.get("workout_context") or {}),
                            "current_exercise_index": workout_update.get(
                                "current_exercise_index",
                                (session_context.get("workout_context") or {}).get("current_exercise_index", 0),
                            ),
                        }

                    await agent_memory_service.save_conversation(
                        db,
                        internal_user_id,
                        "model",
                        agent_reply,
                        agent_name="VoiceRouter",
                        session_id=session_context["session_id"],
                    )

                    await websocket.send_json({"type": "agent_text", "text": agent_reply})
                    if isinstance(workout_update, dict):
                        await websocket.send_json({"type": "workout_update", "data": workout_update})

                    if session_context.get("tts_enabled", True):
                        await websocket.send_json({"type": "state", "status": "speaking"})
                        audio_b64 = await voice_agent_service.generate_tts(
                            agent_reply,
                            language_code=session_context.get("language_code", "en-IN"),
                            speaker=session_context.get("voice", "meera"),
                        )
                        if audio_b64:
                            await websocket.send_json({"type": "audio_out", "data": audio_b64})
                        else:
                            await websocket.send_json({"type": "error", "message": "Failed to generate speech."})

                    await websocket.send_json({"type": "state", "status": "idle"})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected for user %s", user_id)
    except Exception as exc:
        logger.error("WebSocket unhandled error: %s", exc, exc_info=True)
        try:
            await websocket.close(1011)
        except Exception:
            pass
