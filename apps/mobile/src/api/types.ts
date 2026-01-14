/**
 * TrueShift - API Types
 */

export interface UserResponse {
    id: string;
    firebase_uid: string;
    email: string | null;
    display_name: string | null;
    is_active: boolean;
    is_premium: boolean;
    onboarding_completed: boolean;
    consent_status: Record<string, boolean>;
}

export interface ConsentUpdate {
    location_tracking?: boolean;
    health_data?: boolean;
    camera_access?: boolean;
    digital_wellbeing?: boolean;
    ai_coaching?: boolean;
    data_analytics?: boolean;
}

export interface UserProfileUpdate {
    display_name?: string;
    avatar_url?: string;
    fitness_goals?: string[];
    equipment?: string[];
    fitness_level?: string;
}

export interface EventPayload {
    event_type: string;
    payload: Record<string, unknown>;
    timestamp?: string;
    session_id?: string;
    device_info?: Record<string, unknown>;
}

export interface UserState {
    user_id: string;
    last_activity_at: string | null;
    physical: Record<string, unknown>;
    location: Record<string, unknown>;
    digital: Record<string, unknown>;
    goals: string[];
    focus_area: string | null;
}

export interface Recommendation {
    id: string;
    type: string;
    title: string;
    description: string;
    priority: number;
    actions: Record<string, unknown>[];
    confidence: number;
    // ...
}

export interface AICoaching {
    context_summary: Record<string, unknown> | null;
    coaching: Record<string, unknown> | null;
    workout: Record<string, unknown> | null;
    errors: string[];
}

export interface VisionAnalysisResponse {
    status: string;
    data: {
        form_score: number;
        feedback: string;
        issues?: string[];
    };
}

export interface WorkoutGenerationRequest {
    target_muscle_group?: string;
    duration_minutes?: number;
    equipment?: string[];
    fitness_level?: string;
    goals?: string;
}

export interface WorkoutPlanResponse {
    id: string;
    created_at: string;
    status: string;
    plan_data: {
        overview: string;
        exercises: {
            name: string;
            sets: number | string;
            reps: number | string;
            rest_seconds?: number;
            notes?: string;
        }[];
    };
}
