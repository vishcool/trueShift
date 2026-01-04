/**
 * TrueShift - Offline Cache Service
 * 
 * Manages offline-first caching for user state and recommendations.
 * Uses AsyncStorage for persistence.
 */

import AsyncStorage from '@react-native-async-storage/async-storage';

// Cache keys
const CACHE_PREFIX = '@trueshift/cache/';
const CACHE_KEYS = {
    USER_STATE: `${CACHE_PREFIX}user_state`,
    RECOMMENDATIONS: `${CACHE_PREFIX}recommendations`,
    AI_COACHING: `${CACHE_PREFIX}ai_coaching`,
    LAST_SYNC: `${CACHE_PREFIX}last_sync`,
} as const;

// Cache TTL (time to live) in milliseconds
const CACHE_TTL = {
    USER_STATE: 1000 * 60 * 5, // 5 minutes
    RECOMMENDATIONS: 1000 * 60 * 15, // 15 minutes
    AI_COACHING: 1000 * 60 * 30, // 30 minutes
};

interface CacheItem<T> {
    data: T;
    timestamp: number;
    expiresAt: number;
}

class OfflineCache {
    /**
     * Set cached data with TTL
     */
    async set<T>(key: string, data: T, ttlMs: number): Promise<void> {
        const now = Date.now();
        const item: CacheItem<T> = {
            data,
            timestamp: now,
            expiresAt: now + ttlMs,
        };
        await AsyncStorage.setItem(key, JSON.stringify(item));
    }

    /**
     * Get cached data if not expired
     */
    async get<T>(key: string): Promise<T | null> {
        try {
            const raw = await AsyncStorage.getItem(key);
            if (!raw) return null;

            const item: CacheItem<T> = JSON.parse(raw);

            // Check expiration
            if (Date.now() > item.expiresAt) {
                await this.remove(key);
                return null;
            }

            return item.data;
        } catch {
            return null;
        }
    }

    /**
     * Get cached data even if expired (for offline fallback)
     */
    async getStale<T>(key: string): Promise<{ data: T; isStale: boolean } | null> {
        try {
            const raw = await AsyncStorage.getItem(key);
            if (!raw) return null;

            const item: CacheItem<T> = JSON.parse(raw);
            const isStale = Date.now() > item.expiresAt;

            return { data: item.data, isStale };
        } catch {
            return null;
        }
    }

    /**
     * Remove cached item
     */
    async remove(key: string): Promise<void> {
        await AsyncStorage.removeItem(key);
    }

    /**
     * Clear all cache
     */
    async clearAll(): Promise<void> {
        const keys = await AsyncStorage.getAllKeys();
        const cacheKeys = keys.filter((k) => k.startsWith(CACHE_PREFIX));
        await AsyncStorage.multiRemove(cacheKeys);
    }

    /**
     * Get cache age in seconds
     */
    async getAge(key: string): Promise<number | null> {
        try {
            const raw = await AsyncStorage.getItem(key);
            if (!raw) return null;

            const item: CacheItem<unknown> = JSON.parse(raw);
            return Math.floor((Date.now() - item.timestamp) / 1000);
        } catch {
            return null;
        }
    }
}

// Singleton instance
const cache = new OfflineCache();

// =============================================================================
// High-Level Cache Functions
// =============================================================================

export const offlineCache = {
    // User State
    userState: {
        set: async (data: unknown) =>
            cache.set(CACHE_KEYS.USER_STATE, data, CACHE_TTL.USER_STATE),

        get: async () =>
            cache.get(CACHE_KEYS.USER_STATE),

        getStale: async () =>
            cache.getStale(CACHE_KEYS.USER_STATE),
    },

    // Recommendations
    recommendations: {
        set: async (data: unknown) =>
            cache.set(CACHE_KEYS.RECOMMENDATIONS, data, CACHE_TTL.RECOMMENDATIONS),

        get: async () =>
            cache.get(CACHE_KEYS.RECOMMENDATIONS),

        getStale: async () =>
            cache.getStale(CACHE_KEYS.RECOMMENDATIONS),
    },

    // AI Coaching
    aiCoaching: {
        set: async (data: unknown) =>
            cache.set(CACHE_KEYS.AI_COACHING, data, CACHE_TTL.AI_COACHING),

        get: async () =>
            cache.get(CACHE_KEYS.AI_COACHING),

        getStale: async () =>
            cache.getStale(CACHE_KEYS.AI_COACHING),
    },

    // Last sync timestamp
    lastSync: {
        set: async () =>
            AsyncStorage.setItem(CACHE_KEYS.LAST_SYNC, Date.now().toString()),

        get: async (): Promise<Date | null> => {
            const ts = await AsyncStorage.getItem(CACHE_KEYS.LAST_SYNC);
            return ts ? new Date(parseInt(ts, 10)) : null;
        },
    },

    // Clear all
    clearAll: () => cache.clearAll(),
};
