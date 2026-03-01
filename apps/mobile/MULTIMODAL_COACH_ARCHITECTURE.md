# TrueShift Multimodal Coach Architecture

## Goal
Deliver a single coaching experience that combines:
- Real-time voice STT/TTS
- Text chat
- Fitness planning (workout + diet + recovery)
- Context-aware recommendations from user state

## Current Mobile Architecture
- `HomeScreen.tsx` is the multimodal hub.
- Modes are explicit: `general | workout | diet | recovery`.
- Text requests call `POST /agent/chat` with `coach_mode` and state context.
- Voice calls `WS /voice/ws/{firebase_uid}` and sends `context` events (`mode`, `language_code`).

## Voice Session Flow
1. App opens WebSocket with user identity (`firebase_uid`) and optional query context.
2. App sends `context` frame when connection opens or mode/language changes.
3. User records audio in a bounded segment.
4. App sends `audio` + `stop` frames.
5. Backend performs STT, routes response generation by mode, stores memory, returns:
   - `transcript`
   - `agent_text`
   - `audio_out`
   - `state`

## Backend Responsibilities
- Voice route resolves Firebase UID to internal user UUID.
- User-state and conversation logs are stored using internal UUID.
- Agent route returns structured fields (`response`, `action`, `data`) to support UI actions.

## Coding Standards Applied
- Typed API contracts for chat and voice session context.
- Explicit mode enums in UI to avoid string drift.
- Isolated side effects for socket/audio lifecycle.
- Defensive handling for transient failures (network, permission, recording state).

## Implemented In This Iteration
1. Added `/diet/generate` with dedicated diet schemas and macro/meal template response.
2. Added chunk-based streaming upload from mobile voice recording (`audio_chunk` protocol).
3. Added voice session segmentation and persisted logs with `session_id` plus session history APIs.
4. Added user voice preferences (`/voice/preferences`) and preference sync from mobile.
5. Moved repeated chips/cards/bubbles into shared UI components.

## Next Iterations
1. Upgrade from chunk-upload streaming to server-pushed partial transcript streaming per chunk.
2. Add a dedicated diet planner screen with editable calorie/macro goals and weekly plan view.
3. Add migration support for existing databases where `preferences.voice_preferences` is missing.
