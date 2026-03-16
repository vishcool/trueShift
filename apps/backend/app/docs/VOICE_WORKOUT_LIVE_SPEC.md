# Voice Workout Live Spec

## Goal

Keep one voice coach session active through the workout, let the user speak naturally between sets, and turn recognized workout actions into real tracked data.

## Current Contract

Client websocket messages:

- `context`
- `start`
- `audio_chunk`
- `process_segment`
- `stop`

Server websocket messages:

- `status`
- `state`
- `transcript_partial`
- `transcript`
- `agent_text`
- `workout_update`
- `audio_out`
- `error`

## Workout-Aware Voice Context

The mobile client should attach `workout_context` inside the `context` message:

```json
{
  "session_id": "workout-123",
  "current_exercise_index": 1,
  "exercises": [
    {
      "name": "Goblet Squat",
      "performed_sets": [
        { "set_number": 1, "weight": "20", "reps": "10" }
      ]
    }
  ]
}
```

This allows the voice agent to:

- log a spoken set against the active exercise
- advance to the next exercise
- raise a recovery warning when the user reports pain or dizziness

## Voice Workout Update Shapes

### Log set

```json
{
  "type": "log_set",
  "exercise_index": 0,
  "current_exercise_index": 0,
  "set_number": 2,
  "reps": "10",
  "weight": "22.5",
  "completed_at": "2026-03-15T12:30:00Z",
  "source": "voice"
}
```

### Advance exercise

```json
{
  "type": "advance_exercise",
  "exercise_index": 1,
  "current_exercise_index": 1,
  "completed_at": "2026-03-15T12:31:00Z"
}
```

### Recovery flag

```json
{
  "type": "recovery_flag",
  "exercise_index": 1,
  "current_exercise_index": 1,
  "note": "I feel sharp pain in my shoulder",
  "completed_at": "2026-03-15T12:31:20Z"
}
```

## Persistence Rules

When a voice turn completes:

- store the transcript and reply in `conversation_logs`
- write `voice.session_started` once per started voice session
- write `voice.turn_completed` once per processed user turn

When a workout update is extracted:

- `log_set` must also emit `workout.set_logged`
- use the active workout session id as `session_id` when available
- use deterministic `correlation_id` values so retries do not double count

## Dashboard Implications

This gives the system two dependable sources:

- in-session UI state from the mobile workout session store
- persisted event trail from backend event ingestion

Completed workout summaries still come from `workout.record`, but voice-driven set logging is now available before the session ends for live state and future dashboard work.

## Next Recommended Iterations

1. Build a `live session` dashboard query that reads `workout.started`, `workout.set_logged`, and `voice.turn_completed`.
2. Add interruption support so TTS stops immediately when the user speaks again.
3. Add form-analysis events so voice, camera, and workout state can converge on the same session timeline.
