/**
 * TrueShift - Real API Client
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import * as SecureStore from 'expo-secure-store';
import { UserResponse, ConsentUpdate, EventPayload, UserState, Recommendation, AICoaching, VisionAnalysisResponse, UserProfileUpdate, WorkoutGenerationRequest, WorkoutPlanResponse } from './types';

// API Configuration
const API_BASE_URL = __DEV__
    ? 'http://localhost:8000/api/v1'
    : 'https://api.trueshift.app/api/v1';

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
                const token = await SecureStore.getItemAsync(AUTH_TOKEN_KEY);
                if (token) {
                    config.headers.Authorization = `Bearer ${token}`;
                }
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
        register: (displayName?: string) =>
            apiClient.post<UserResponse>('/auth/register', { display_name: displayName }),

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
        generate: (data: WorkoutGenerationRequest) =>
            apiClient.post<WorkoutPlanResponse>('/workout/generate', data),

        log: (planId: string, completionData: Record<string, unknown>) =>
            apiClient.post<WorkoutPlanResponse>('/workout/log', { plan_id: planId, completion_data: completionData }),
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
