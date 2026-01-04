/**
 * TrueShift - useAuth Hook
 * 
 * Authentication hook for Firebase auth integration.
 */

import { useCallback } from 'react';
import { useAuthStore } from '../store/authStore';
import { api, authToken, UserResponse } from '../api/client';

interface UseAuthResult {
    user: UserResponse | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;
    login: (firebaseToken: string) => Promise<void>;
    logout: () => Promise<void>;
    updateConsent: (consents: Record<string, boolean>) => Promise<void>;
}

export function useAuth(): UseAuthResult {
    const {
        user,
        isAuthenticated,
        isLoading,
        error,
        setUser,
        setToken,
        logout: storeLogout,
        updateConsent: storeUpdateConsent,
    } = useAuthStore();

    /**
     * Login with Firebase token
     */
    const login = useCallback(async (firebaseToken: string) => {
        // Store the token
        await setToken(firebaseToken);

        // Register/login with backend
        const response = await api.auth.register();
        setUser(response.data);
    }, [setToken, setUser]);

    /**
     * Logout
     */
    const logout = useCallback(async () => {
        await storeLogout();
    }, [storeLogout]);

    /**
     * Update consent preferences
     */
    const updateConsent = useCallback(async (consents: Record<string, boolean>) => {
        await storeUpdateConsent(consents);
    }, [storeUpdateConsent]);

    return {
        user,
        isAuthenticated,
        isLoading,
        error,
        login,
        logout,
        updateConsent,
    };
}
