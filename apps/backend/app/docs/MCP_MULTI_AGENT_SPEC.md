# TrueShift MCP + Multi-Agent Spec

## Goal
Create a stable contract for planner-driven coaching, live conversations, and workout tracking so future agents can inspect the same specs and improve the system without architectural drift.

## Core Principles
- Use immutable events as the system of record.
- Resolve every authenticated user to one canonical internal UUID before any memory, state, or agent work.
- Let a planner decide which specialist path leads the turn.
- Expose capabilities through MCP-style tools instead of hidden service coupling.
- Keep live conversation state explicit, session-scoped, and auditable.

## Agent Roles
- `PlannerAgent`
  Chooses the primary domain for the current turn: `workout | recovery | mental | nutrition | coaching`.
- `ContextAgent`
  Summarizes readiness, freshness of data, and risks.
- `WorkoutAgent`
  Produces or adapts workouts with progression constraints.
- `RecoveryAgent`
  Reduces risk and adjusts training load.
- `MentalAgent`
  Handles adherence, stress, and motivation support.
- `DecisionLayer`
  Combines planner + specialist outputs into one user-facing action.

## MCP Tool Contracts
- `get_user_state(user_id)`
- `get_progress_dashboard(user_id)`
- `get_recent_workouts(user_id, limit)`
- `get_live_session(session_id)`
- `create_workout_plan(user_id, constraints)`
- `log_workout_event(user_id, event)`
- `store_memory(user_id, memory_update)`
- `get_voice_preferences(user_id)`

## Live Conversation Flow
1. Client opens one long-lived voice session.
2. Partial audio is streamed and transcribed.
3. PlannerAgent inspects transcript + mode + state.
4. Relevant tools are called through the tool layer.
5. Specialist agents generate structured proposals.
6. Decision layer chooses one response and one next action.
7. Response is emitted as text, optional TTS, and structured metadata.
8. Conversation turn and side effects are recorded as events.

## Event Contracts
- `workout.started`
- `workout.completed`
- `workout.exercise_logged`
- `session.started`
- `session.ended`
- `voice.turn_started`
- `voice.partial_transcript`
- `voice.turn_completed`
- `ai.coaching_delivered`
- `ai.feedback_received`

## Idempotency Rules
- Every mobile-originated event should send a `correlation_id`.
- Backend must return the existing event when the same `(user_id, correlation_id)` is retried.
- Session IDs are opaque strings, not UUID-only fields.

## Planning Output Contract
```json
{
  "primary_domain": "workout",
  "goals": ["create_or_adjust_workout", "preserve_progression"],
  "delegates": ["context", "workout", "coaching"],
  "confidence": 0.86
}
```

## Next Iterations
- Add a safety/critic agent for contradiction checking.
- Add freshness/confidence scoring to `UserState`.
- Promote the MCP tool layer from spec to executable interfaces.
- Move voice from chunk-upload to partial streaming with interruption support.
