/**
 * TrueShift - useLocation Hook
 * 
 * Custom hook for location tracking with context detection.
 */

import { useEffect, useState, useCallback } from 'react';
import * as Location from 'expo-location';

import { checkLocationPermission, requestLocationPermission } from '../utils/permissions';
import { trackEvent } from '../services/BackgroundSync';

export interface LocationData {
    latitude: number;
    longitude: number;
    accuracy: number | null;
    timestamp: number;
}

export interface LocationContext {
    type: 'home' | 'gym' | 'park' | 'office' | 'outdoors' | 'unknown';
    name?: string;
}

interface UseLocationResult {
    location: LocationData | null;
    context: LocationContext;
    isLoading: boolean;
    error: string | null;
    hasPermission: boolean;
    requestPermission: () => Promise<boolean>;
    refresh: () => Promise<void>;
}

export function useLocation(): UseLocationResult {
    const [location, setLocation] = useState<LocationData | null>(null);
    const [context, setContext] = useState<LocationContext>({ type: 'unknown' });
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [hasPermission, setHasPermission] = useState(false);

    // Check permission on mount
    useEffect(() => {
        checkPermissionStatus();
    }, []);

    // Start watching location when permission granted
    useEffect(() => {
        if (!hasPermission) return;

        let subscription: Location.LocationSubscription | null = null;

        const startWatching = async () => {
            try {
                subscription = await Location.watchPositionAsync(
                    {
                        accuracy: Location.Accuracy.Balanced,
                        timeInterval: 60000, // Every minute
                        distanceInterval: 100, // Or every 100 meters
                    },
                    (loc) => {
                        const newLocation: LocationData = {
                            latitude: loc.coords.latitude,
                            longitude: loc.coords.longitude,
                            accuracy: loc.coords.accuracy,
                            timestamp: loc.timestamp,
                        };
                        setLocation(newLocation);
                        setIsLoading(false);

                        // Track location update event
                        trackEvent('location.updated', {
                            latitude: newLocation.latitude,
                            longitude: newLocation.longitude,
                        });
                    },
                );
            } catch (err) {
                setError('Failed to watch location');
                setIsLoading(false);
            }
        };

        startWatching();

        return () => {
            subscription?.remove();
        };
    }, [hasPermission]);

    const checkPermissionStatus = async () => {
        const status = await checkLocationPermission();
        setHasPermission(status.granted);
        if (!status.granted) {
            setIsLoading(false);
        }
    };

    const requestPermissionHandler = useCallback(async () => {
        const granted = await requestLocationPermission();
        setHasPermission(granted);
        return granted;
    }, []);

    const refresh = useCallback(async () => {
        if (!hasPermission) return;

        setIsLoading(true);
        try {
            const loc = await Location.getCurrentPositionAsync({});
            setLocation({
                latitude: loc.coords.latitude,
                longitude: loc.coords.longitude,
                accuracy: loc.coords.accuracy,
                timestamp: loc.timestamp,
            });
        } catch (err) {
            setError('Failed to get location');
        } finally {
            setIsLoading(false);
        }
    }, [hasPermission]);

    return {
        location,
        context,
        isLoading,
        error,
        hasPermission,
        requestPermission: requestPermissionHandler,
        refresh,
    };
}
