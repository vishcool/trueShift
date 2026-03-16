import { create } from 'zustand';

import { WorkoutPerformedSet } from '../api/client';

interface WorkoutExercise {
    name: string;
    sets?: number | string;
    reps?: number | string;
    rest_seconds?: number;
    notes?: string;
}

interface WorkoutSessionState {
    sessionId: string | null;
    exercises: WorkoutExercise[];
    logs: Record<number, WorkoutPerformedSet[]>;
    currentExerciseIndex: number;
    initializeSession: (exercises: WorkoutExercise[], sessionId?: string) => void;
    updateLog: (exerciseIdx: number, setIdx: number, field: 'weight' | 'reps', value: string) => void;
    applyVoiceUpdate: (update: Record<string, unknown>) => void;
    clearSession: () => void;
}

function createSessionId() {
    return `workout-${Date.now()}`;
}

export const useWorkoutSessionStore = create<WorkoutSessionState>((set) => ({
    sessionId: null,
    exercises: [],
    logs: {},
    currentExerciseIndex: 0,
    initializeSession: (exercises, sessionId) =>
        set((state) => {
            if (state.sessionId && state.exercises.length > 0) {
                return state;
            }
            return {
                sessionId: sessionId || createSessionId(),
                exercises,
                logs: {},
                currentExerciseIndex: 0,
            };
        }),
    updateLog: (exerciseIdx, setIdx, field, value) =>
        set((state) => {
            const currentExLogs = state.logs[exerciseIdx] || [];
            const newExLogs = [...currentExLogs];
            const existing = newExLogs[setIdx] || {
                set_number: setIdx + 1,
                weight: '',
                reps: '',
            };

            newExLogs[setIdx] = {
                ...existing,
                [field]: value,
            };

            return {
                logs: {
                    ...state.logs,
                    [exerciseIdx]: newExLogs,
                },
            };
        }),
    applyVoiceUpdate: (update) =>
        set((state) => {
            const type = String(update.type || '');
            const nextState: Partial<WorkoutSessionState> = {};

            if (typeof update.current_exercise_index === 'number') {
                nextState.currentExerciseIndex = update.current_exercise_index;
            }

            if (type === 'log_set') {
                const exerciseIdx = typeof update.exercise_index === 'number' ? update.exercise_index : state.currentExerciseIndex;
                const setNumber = typeof update.set_number === 'number' ? update.set_number : (state.logs[exerciseIdx]?.length || 0) + 1;
                const currentExLogs = [...(state.logs[exerciseIdx] || [])];
                currentExLogs[setNumber - 1] = {
                    set_number: setNumber,
                    weight: String(update.weight ?? ''),
                    reps: String(update.reps ?? ''),
                    completed_at: typeof update.completed_at === 'string' ? update.completed_at : new Date().toISOString(),
                };

                nextState.logs = {
                    ...state.logs,
                    [exerciseIdx]: currentExLogs,
                };
            }

            if (type === 'advance_exercise' && typeof update.exercise_index === 'number') {
                nextState.currentExerciseIndex = update.exercise_index;
            }

            return nextState as WorkoutSessionState;
        }),
    clearSession: () =>
        set({
            sessionId: null,
            exercises: [],
            logs: {},
            currentExerciseIndex: 0,
        }),
}));
