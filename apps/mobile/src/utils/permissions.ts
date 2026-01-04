/**
 * TrueShift - Permissions Utility
 * 
 * Centralized permission handling for location, camera, notifications.
 * Supports progressive permission requesting.
 */

import * as Location from 'expo-location';
import * as Notifications from 'expo-notifications';
import { Camera } from 'expo-camera';
import { Alert, Linking, Platform } from 'react-native';

export type PermissionType =
    | 'location_foreground'
    | 'location_background'
    | 'camera'
    | 'notifications';

export interface PermissionStatus {
    granted: boolean;
    canAskAgain: boolean;
}

// =============================================================================
// Permission Checkers
// =============================================================================

/**
 * Check location permission status
 */
export async function checkLocationPermission(): Promise<PermissionStatus> {
    const { status, canAskAgain } = await Location.getForegroundPermissionsAsync();
    return {
        granted: status === 'granted',
        canAskAgain,
    };
}

/**
 * Check background location permission
 */
export async function checkBackgroundLocationPermission(): Promise<PermissionStatus> {
    const { status, canAskAgain } = await Location.getBackgroundPermissionsAsync();
    return {
        granted: status === 'granted',
        canAskAgain,
    };
}

/**
 * Check camera permission status
 */
export async function checkCameraPermission(): Promise<PermissionStatus> {
    const { status, canAskAgain } = await Camera.getCameraPermissionsAsync();
    return {
        granted: status === 'granted',
        canAskAgain,
    };
}

/**
 * Check notification permission status
 */
export async function checkNotificationPermission(): Promise<PermissionStatus> {
    const { status, canAskAgain } = await Notifications.getPermissionsAsync();
    return {
        granted: status === 'granted',
        canAskAgain,
    };
}

// =============================================================================
// Permission Requesters
// =============================================================================

/**
 * Request foreground location permission
 */
export async function requestLocationPermission(): Promise<boolean> {
    const { status } = await Location.requestForegroundPermissionsAsync();
    return status === 'granted';
}

/**
 * Request background location permission
 * Must have foreground permission first
 */
export async function requestBackgroundLocationPermission(): Promise<boolean> {
    // First ensure foreground is granted
    const foreground = await checkLocationPermission();
    if (!foreground.granted) {
        const granted = await requestLocationPermission();
        if (!granted) return false;
    }

    const { status } = await Location.requestBackgroundPermissionsAsync();
    return status === 'granted';
}

/**
 * Request camera permission
 */
export async function requestCameraPermission(): Promise<boolean> {
    const { status } = await Camera.requestCameraPermissionsAsync();
    return status === 'granted';
}

/**
 * Request notification permission
 */
export async function requestNotificationPermission(): Promise<boolean> {
    const { status } = await Notifications.requestPermissionsAsync();
    return status === 'granted';
}

// =============================================================================
// Progressive Permission Flow
// =============================================================================

interface PermissionConfig {
    type: PermissionType;
    title: string;
    message: string;
    required: boolean;
}

const PERMISSION_CONFIGS: PermissionConfig[] = [
    {
        type: 'notifications',
        title: 'Stay Updated',
        message: 'Enable notifications to receive coaching reminders and workout suggestions.',
        required: false,
    },
    {
        type: 'location_foreground',
        title: 'Location Access',
        message: 'TrueShift uses your location to provide context-aware workout recommendations when you\'re at a gym or park.',
        required: true,
    },
    {
        type: 'camera',
        title: 'Camera Access',
        message: 'Use your camera to capture exercise form for AI-powered feedback.',
        required: false,
    },
];

/**
 * Request a specific permission with explanation
 */
export async function requestPermissionWithExplanation(
    type: PermissionType,
): Promise<boolean> {
    const config = PERMISSION_CONFIGS.find((c) => c.type === type);
    if (!config) return false;

    return new Promise((resolve) => {
        Alert.alert(
            config.title,
            config.message,
            [
                {
                    text: 'Not Now',
                    style: 'cancel',
                    onPress: () => resolve(false),
                },
                {
                    text: 'Allow',
                    onPress: async () => {
                        let granted = false;
                        switch (type) {
                            case 'location_foreground':
                                granted = await requestLocationPermission();
                                break;
                            case 'location_background':
                                granted = await requestBackgroundLocationPermission();
                                break;
                            case 'camera':
                                granted = await requestCameraPermission();
                                break;
                            case 'notifications':
                                granted = await requestNotificationPermission();
                                break;
                        }
                        resolve(granted);
                    },
                },
            ],
        );
    });
}

/**
 * Open app settings for manual permission grant
 */
export function openAppSettings(): void {
    if (Platform.OS === 'ios') {
        Linking.openURL('app-settings:');
    } else {
        Linking.openSettings();
    }
}

/**
 * Get all permission statuses
 */
export async function getAllPermissionStatuses(): Promise<Record<PermissionType, PermissionStatus>> {
    const [location, backgroundLocation, camera, notifications] = await Promise.all([
        checkLocationPermission(),
        checkBackgroundLocationPermission(),
        checkCameraPermission(),
        checkNotificationPermission(),
    ]);

    return {
        location_foreground: location,
        location_background: backgroundLocation,
        camera,
        notifications,
    };
}
