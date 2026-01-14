/**
 * TrueShift - Auth Store
 * 
 * Global authentication state using Zustand.
 * Manages user session and consent status.
 */

import { create } from 'zustand';
import { api, authToken, UserResponse, UserProfileUpdate } from '../api/client';

interface AuthState {
    // State
    user: UserResponse | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;

    // Actions
    initialize: () => Promise<void>;
    setUser: (user: UserResponse) => void;
    setToken: (token: string) => Promise<void>;
    logout: () => Promise<void>;
    updateConsent: (consents: Record<string, boolean>) => Promise<void>;
    updateProfile: (data: UserProfileUpdate) => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
    // Initial state
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,

    // Initialize - check for existing session
    initialize: async () => {
        try {
            set({ isLoading: true, error: null });

            const token = await authToken.get();
            if (!token) {
                set({ isLoading: false, isAuthenticated: false });
                return;
            }

            // Validate token by fetching user
            const response = await api.auth.getMe();
            set({
                user: response.data,
                isAuthenticated: true,
                isLoading: false,
            });
        } catch (error) {
            // Token invalid or expired
            await authToken.clear();
            set({
                user: null,
                isAuthenticated: false,
                isLoading: false,
                error: 'Session expired',
            });
        }
    },

    // Set user data
    setUser: (user) => {
        set({ user, isAuthenticated: true, error: null });
    },

    // Set auth token
    setToken: async (token) => {
        await authToken.set(token);
    },

    // Logout
    logout: async () => {
        await authToken.clear();
        set({
            user: null,
            isAuthenticated: false,
            error: null,
        });
    },

    // Update consent preferences
    updateConsent: async (consents) => {
        try {
            const response = await api.auth.updateConsent(consents);
            const currentUser = get().user;
            if (currentUser) {
                set({
                    user: {
                        ...currentUser,
                        consent_status: response.data.consents,
                    },
                });
            }
        } catch (error) {
            set({ error: 'Failed to update consent' });
            throw error;
        }
    },

    // Update profile
    updateProfile: async (data: UserProfileUpdate) => {
        try {
            const response = await api.auth.updateProfile(data);
            set({ user: response.data });
        } catch (error) {
            set({ error: 'Failed to update profile' });
            throw error;
        }
    },
}));
