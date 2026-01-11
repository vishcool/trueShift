/**
 * TrueShift - Mock API Client
 */

import * as SecureStore from 'expo-secure-store';
import { UserResponse, ConsentUpdate, EventPayload, UserState, Recommendation, AICoaching } from './types';

const AUTH_TOKEN_KEY = 'auth_token';

// Mock Data Helper
const delay = <T>(ms: number, data: T): Promise<{ data: T }> =>
    new Promise(resolve => setTimeout(() => resolve({ data }), ms));

const MOCK_USER: UserResponse = {
    id: 'user_123',
    firebase_uid: 'firebase_123',
    email: 'mock@trueshift.app',
    display_name: 'Test User',
    is_active: true,
    is_premium: false,
    onboarding_completed: true,
    consent_status: {
        location_tracking: true,
        health_data: true,
    },
};

export const api = {
    // Auth
    auth: {
        register: (displayName?: string) =>
            delay(1000, { ...MOCK_USER, display_name: displayName || 'New User' }),

        getMe: () =>
            delay(500, MOCK_USER),

        getConsent: () =>
            delay(500, {
                consents: MOCK_USER.consent_status,
                updated_at: new Date().toISOString()
            }),

        updateConsent: (consents: ConsentUpdate) =>
            delay(500, { consents: { ...MOCK_USER.consent_status, ...consents } }),
    },

    // Events
    events: {
        send: (event: EventPayload) =>
            delay(200, { status: 'ok', event_id: 'evt_' + Date.now() }),

        sendBatch: (events: EventPayload[]) =>
            delay(200, { status: 'ok', count: events.length }),

        getTypes: () =>
            delay(500, { event_types: ['app_open', 'workout_start', 'focus_session'] }),
    },

    // State & AI
    state: {
        get: () =>
            delay(500, {
                user_id: MOCK_USER.id,
                last_activity_at: new Date().toISOString(),
                physical: { steps: 5430, kCal: 450 },
                location: { current: 'Home' },
                digital: { screen_time: '2h 15m' },
                goals: ['Walk 10k steps', 'Deep work 2h'],
                focus_area: 'productivity',
            } as UserState),

        getRecommendations: (limit = 3) =>
            delay(800, {
                count: 3,
                recommendations: [
                    {
                        id: 'rec_1',
                        type: 'wellbeing',
                        title: 'Take a break',
                        description: 'You have been active for 2 hours.',
                        priority: 1,
                        actions: [],
                        confidence: 0.9,
                    },
                    {
                        id: 'rec_2',
                        type: 'fitness',
                        title: 'Go for a walk',
                        description: 'Weather is nice now.',
                        priority: 2,
                        actions: [],
                        confidence: 0.85,
                    },
                ] as Recommendation[],
            }),

        getAICoaching: () =>
            delay(1000, {
                context_summary: { status: 'active' },
                coaching: { message: 'Great progress today! Keep it up.' },
                workout: null,
                errors: [],
            } as AICoaching),

        getWorkout: () =>
            delay(1000, { plan: 'Light cardio', duration: '30m' }),
    },

    // Health
    health: {
        check: () => delay(200, { status: 'ok', version: '1.0.0-mock' }),
    },

    // Vision (Mock)
    vision: {
        analyzeChunk: (data: FormData) =>
            delay(300, {
                status: 'success',
                data: {
                    form_score: 85 + Math.random() * 10,
                    feedback: Math.random() > 0.7 ? "Keep your back straight" : "Good form",
                    issues: Math.random() > 0.8 ? ["posture_warning"] : []
                }
            })
    },
};

export const authToken = {
    set: async (token: string) => {
        await SecureStore.setItemAsync(AUTH_TOKEN_KEY, token);
    },

    get: async () => {
        return SecureStore.getItemAsync(AUTH_TOKEN_KEY);
    },

    clear: async () => {
        await SecureStore.deleteItemAsync(AUTH_TOKEN_KEY);
    },
};
