# TrueShift Event and Tracking Spec

## Goal
Support reliable workout learning, live coaching, and future planning by capturing more than just end-of-session summaries.

## Workout Session Lifecycle
1. `workout.started`
2. `workout.exercise_logged` for each exercise or set group
3. `workout.completed`

## Recommended Payloads

### `workout.started`
```json
{
  "workout_plan_id": "optional-plan-id",
  "workout_type": "strength",
  "planned_duration_minutes": 45
}
```

### `workout.exercise_logged`
```json
{
  "name": "Squat",
  "performed_sets": [
    { "weight": 60, "reps": 10, "rpe": 8 }
  ]
}
```

### `workout.completed`
```json
{
  "workout_type": "strength",
  "duration_minutes": 42,
  "exercise_count": 6
}
```

## Identity Rules
- `firebase_uid` is only for authentication lookup.
- `users.id` is the canonical key for events, memory, conversations, and plans.

## Correlation Rules
- Mobile should create a stable `correlation_id` per attempted event write.
- Backend should accept retries without double counting.

## Current Implementation Status
- Canonical user ID handling is now enforced in the chat path.
- Workout record/log routes now emit workout completion events.
- Event deduplication uses `(user_id, correlation_id)`.
- The dashboard can now derive weekly minutes, logged sets, total volume, recovery context, and coaching suggestions from stored workout + state data.

## Remaining Gaps
- Per-set event emission should move into the mobile active session flow.
- Weekly load, muscle-group volume, and adherence metrics should be derived from events, not guessed from summaries.
