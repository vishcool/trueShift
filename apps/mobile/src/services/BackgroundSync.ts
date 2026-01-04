/**
 * TrueShift - Background Sync Service
 * 
 * Handles background data synchronization with the backend.
 * Uses Expo BackgroundFetch and TaskManager for periodic sync.
 */

import * as BackgroundFetch from 'expo-background-fetch';
import * as TaskManager from 'expo-task-manager';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { api, EventPayload } from '../api/client';

// Task names
const BACKGROUND_SYNC_TASK = 'TRUESHIFT_BACKGROUND_SYNC';
const EVENT_QUEUE_KEY = '@trueshift/event_queue';

// =============================================================================
// Event Queue Manager
// =============================================================================

interface EventQueueItem {
    id: string;
    event: EventPayload;
    createdAt: string;
    retryCount: number;
}

class EventQueue {
    /**
     * Add event to queue for later sync
     */
    async enqueue(event: EventPayload): Promise<void> {
        const queue = await this.getQueue();
        const item: EventQueueItem = {
            id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            event,
            createdAt: new Date().toISOString(),
            retryCount: 0,
        };
        queue.push(item);
        await this.saveQueue(queue);
    }

    /**
     * Get all queued events
     */
    async getQueue(): Promise<EventQueueItem[]> {
        try {
            const data = await AsyncStorage.getItem(EVENT_QUEUE_KEY);
            return data ? JSON.parse(data) : [];
        } catch {
            return [];
        }
    }

    /**
     * Save queue to storage
     */
    async saveQueue(queue: EventQueueItem[]): Promise<void> {
        await AsyncStorage.setItem(EVENT_QUEUE_KEY, JSON.stringify(queue));
    }

    /**
     * Remove events by IDs
     */
    async remove(ids: string[]): Promise<void> {
        const queue = await this.getQueue();
        const filtered = queue.filter((item) => !ids.includes(item.id));
        await this.saveQueue(filtered);
    }

    /**
     * Mark event for retry
     */
    async markRetry(id: string): Promise<void> {
        const queue = await this.getQueue();
        const item = queue.find((i) => i.id === id);
        if (item) {
            item.retryCount += 1;
            await this.saveQueue(queue);
        }
    }

    /**
     * Get pending count
     */
    async getPendingCount(): Promise<number> {
        const queue = await this.getQueue();
        return queue.length;
    }
}

export const eventQueue = new EventQueue();

// =============================================================================
// Background Sync Task
// =============================================================================

/**
 * Define the background task
 */
TaskManager.defineTask(BACKGROUND_SYNC_TASK, async () => {
    try {
        console.log('[BackgroundSync] Starting sync task');

        // Get queued events
        const queue = await eventQueue.getQueue();

        if (queue.length === 0) {
            console.log('[BackgroundSync] No events to sync');
            return BackgroundFetch.BackgroundFetchResult.NoData;
        }

        // Prepare events for batch send
        const events = queue
            .filter((item) => item.retryCount < 3) // Max 3 retries
            .map((item) => item.event);

        if (events.length === 0) {
            console.log('[BackgroundSync] All events exceeded retry limit');
            return BackgroundFetch.BackgroundFetchResult.Failed;
        }

        // Send batch
        await api.events.sendBatch(events);

        // Remove sent events
        const sentIds = queue
            .filter((item) => item.retryCount < 3)
            .map((item) => item.id);
        await eventQueue.remove(sentIds);

        console.log(`[BackgroundSync] Synced ${events.length} events`);
        return BackgroundFetch.BackgroundFetchResult.NewData;

    } catch (error) {
        console.error('[BackgroundSync] Sync failed:', error);
        return BackgroundFetch.BackgroundFetchResult.Failed;
    }
});

// =============================================================================
// Background Service Initialization
// =============================================================================

/**
 * Register background fetch task
 */
export async function registerBackgroundSync(): Promise<void> {
    try {
        await BackgroundFetch.registerTaskAsync(BACKGROUND_SYNC_TASK, {
            minimumInterval: 60 * 15, // 15 minutes
            stopOnTerminate: false,
            startOnBoot: true,
        });
        console.log('[BackgroundSync] Task registered');
    } catch (error) {
        console.error('[BackgroundSync] Failed to register task:', error);
    }
}

/**
 * Unregister background fetch task
 */
export async function unregisterBackgroundSync(): Promise<void> {
    try {
        await BackgroundFetch.unregisterTaskAsync(BACKGROUND_SYNC_TASK);
        console.log('[BackgroundSync] Task unregistered');
    } catch (error) {
        console.error('[BackgroundSync] Failed to unregister task:', error);
    }
}

/**
 * Check if background fetch is available
 */
export async function checkBackgroundStatus(): Promise<BackgroundFetch.BackgroundFetchStatus> {
    return BackgroundFetch.getStatusAsync();
}

/**
 * Initialize background services
 */
export async function initBackgroundServices(): Promise<void> {
    const status = await checkBackgroundStatus();

    if (status === BackgroundFetch.BackgroundFetchStatus.Available) {
        await registerBackgroundSync();
    } else {
        console.warn('[BackgroundSync] Background fetch not available:', status);
    }
}

// =============================================================================
// Event Tracking Helpers
// =============================================================================

/**
 * Track an event - queues for background sync
 */
export async function trackEvent(
    eventType: string,
    payload: Record<string, unknown> = {},
): Promise<void> {
    const event: EventPayload = {
        event_type: eventType,
        payload,
        timestamp: new Date().toISOString(),
    };

    // Try immediate send, fall back to queue
    try {
        await api.events.send(event);
    } catch {
        // Queue for background sync
        await eventQueue.enqueue(event);
        console.log('[BackgroundSync] Event queued for later sync');
    }
}

/**
 * Force sync immediately
 */
export async function forceSyncNow(): Promise<void> {
    const queue = await eventQueue.getQueue();

    if (queue.length === 0) {
        return;
    }

    const events = queue.map((item) => item.event);
    await api.events.sendBatch(events);
    await eventQueue.remove(queue.map((item) => item.id));
}
