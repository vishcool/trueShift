/**
 * TrueShift - Real API Client
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import * as SecureStore from 'expo-secure-store';
import {
    UserResponse,
    ConsentUpdate,
    EventPayload,
    UserState,
    Recommendation,
    AICoaching,
    VisionAnalysisResponse,
    UserProfileUpdate,
    WorkoutGenerationRequest,
    WorkoutPlanResponse,
    WorkoutRecordPayload,
    AgentChatResponse,
    VoiceSessionContext,
    VoicePreferences,
    VoiceSessionSummary,
    VoiceSessionDetail,
    DietPlanRequest,
    DietPlanResponse,
    ProgressDashboard
} from './types';

// API Configuration
const API_BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? "http://192.168.29.242:8000/api/v1";

const AUTH_TOKEN_KEY = 'auth_token';

/**
 * Create configured axios instance
 */
function createApiClient(): AxiosInstance {
    const client = axios.create({
        baseURL: API_BASE_URL,
        timeout: 30000,
        headers: {
            'Content-Type': 'application/json',
        },
    });

    // Request interceptor - add auth token
    client.interceptors.request.use(
        async (config) => {
            try {
                config.headers.Authorization = `Bearer test`;
                // const token = await SecureStore.getItemAsync(AUTH_TOKEN_KEY);
                // if (token) {
                //     config.headers.Authorization = `Bearer ${token}`;
                // }
            } catch (error) {
                console.warn('Failed to get auth token:', error);
            }
            return config;
        },
        (error) => Promise.reject(error)
    );

    // Response interceptor - handle errors
    client.interceptors.response.use(
        (response) => response,
        async (error: AxiosError) => {
            if (error.response?.status === 401) {
                // Token expired - clear and redirect to login
                await SecureStore.deleteItemAsync(AUTH_TOKEN_KEY);
                // Navigation to login would be handled by auth state
            }
            return Promise.reject(error);
        }
    );

    return client;
}

export const apiClient = createApiClient();

export const api = {
    // Auth
    auth: {
        register: (displayName?: string) => {
            console.log("displayname")
            return apiClient.post<UserResponse>('/auth/register', {
                "display_name": "Test User",
                "email": "test@example.com"
            })
        },
        getMe: () =>
            apiClient.get<UserResponse>('/auth/me'),

        getConsent: () =>
            apiClient.get<{ consents: Record<string, boolean>; updated_at: string }>('/auth/consent'),

        updateConsent: (consents: ConsentUpdate) =>
            apiClient.put('/auth/consent', consents),

        updateProfile: (data: UserProfileUpdate) =>
            apiClient.put<UserResponse>('/auth/me', data),
    },

    // Events
    events: {
        send: (event: EventPayload) =>
            apiClient.post('/events', event),

        sendBatch: (events: EventPayload[]) =>
            apiClient.post('/events/batch', { events }),

        getTypes: () =>
            apiClient.get<{ event_types: string[] }>('/events/types'),
    },

    // State & AI
    state: {
        get: () =>
            apiClient.get<UserState>('/state'),

        getRecommendations: (limit = 3) =>
            apiClient.get<{ recommendations: Recommendation[]; count: number }>(
                `/state/recommendations?limit=${limit}`
            ),

        getAICoaching: () =>
            apiClient.get<AICoaching>('/state/ai/coaching'),

        getDashboard: () =>
            apiClient.get<ProgressDashboard>('/state/dashboard'),

        getWorkout: () =>
            apiClient.get('/state/ai/workout'),
    },

    // Health
    health: {
        check: () =>
            apiClient.get('/health'),
    },

    // Vision
    vision: {
        analyzeChunk: (data: FormData) =>
            apiClient.post<VisionAnalysisResponse>('/vision/analyze-chunk', data, {
                headers: { 'Content-Type': 'multipart/form-data' }
            }),
    },

    // Workout
    workout: {
        record: (data: WorkoutRecordPayload) =>
            apiClient.post<WorkoutPlanResponse>('/workout/record', data),

        generate: (data: WorkoutGenerationRequest) =>
            apiClient.post<WorkoutPlanResponse>('/workout/generate', data),

        generateWithVision: (imageFile: any, params?: WorkoutGenerationRequest) => {
            const formData = new FormData();
            formData.append('file', {
                uri: imageFile.uri,
                name: 'equipment.jpg',
                type: 'image/jpeg',
            } as any);

            if (params?.duration_minutes) formData.append('duration_minutes', String(params.duration_minutes));
            if (params?.fitness_level) formData.append('fitness_level', params.fitness_level);
            if (params?.goals) formData.append('goals', params.goals);

            return apiClient.post<WorkoutPlanResponse>('/workout/generate-with-vision', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
        },

        log: (planId: string, completionData: Record<string, unknown>) =>
            apiClient.post<WorkoutPlanResponse>('/workout/log', { plan_id: planId, completion_data: completionData }),

        getHistory: () =>
            apiClient.get<WorkoutPlanResponse[]>('/workout/history'),
    },

    // Agent
    agent: {
        chat: (message: string, context?: any) =>
            apiClient.post<AgentChatResponse>('/agent/chat', { message, context }),
    },

    // Voice WebSocket
    voice: {
        createSocket: (userId: string, context?: VoiceSessionContext) => {
            // Convert http(s):// to ws(s)://
            const wsPre = API_BASE_URL.replace(/^http/, 'ws');
            const query = new URLSearchParams();
            if (context?.mode) {
                query.set('mode', context.mode);
            }
            if (context?.language_code) {
                query.set('language_code', context.language_code);
            }
            if (context?.voice) {
                query.set('voice', context.voice);
            }
            if (typeof context?.tts_enabled === 'boolean') {
                query.set('tts_enabled', String(context.tts_enabled));
            }
            if (context?.session_id) {
                query.set('session_id', context.session_id);
            }
            const queryString = query.toString();
            const wsUrl = `${wsPre}/voice/ws/${userId}${queryString ? `?${queryString}` : ''}`;
            return new WebSocket(wsUrl);
        },
        getPreferences: () =>
            apiClient.get<VoicePreferences>('/voice/preferences'),
        updatePreferences: (payload: Partial<VoicePreferences>) =>
            apiClient.put<VoicePreferences>('/voice/preferences', payload),
        getSessions: () =>
            apiClient.get<VoiceSessionSummary[]>('/voice/sessions'),
        getSessionDetail: (sessionId: string) =>
            apiClient.get<VoiceSessionDetail>(`/voice/sessions/${sessionId}`),
    },

    diet: {
        generate: (payload: DietPlanRequest) =>
            apiClient.post<DietPlanResponse>('/diet/generate', payload),
    }
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
