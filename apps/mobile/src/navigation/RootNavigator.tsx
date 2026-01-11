/**
 * TrueShift - Root Navigator
 * 
 * Main navigation structure for the app.
 */

import React from 'react';
import { ActivityIndicator, View, StyleSheet } from 'react-native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { useAuth } from '../hooks/useAuth';

// Screens (to be implemented)
import { HomeScreen } from '../screens/HomeScreen';
import { LoginScreen } from '../screens/LoginScreen';
import { OnboardingScreen } from '../screens/OnboardingScreen';
import VisionRecordingScreen from '../screens/VisionRecordingScreen';

export type RootStackParamList = {
    Login: undefined;
    Onboarding: undefined;
    Home: undefined;
    Vision: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

export function RootNavigator() {
    const { isAuthenticated, isLoading, user } = useAuth();

    // Show loading while checking auth state
    if (isLoading) {
        return (
            <View style={styles.loading}>
                <ActivityIndicator size="large" color="#6366F1" />
            </View>
        );
    }

    return (
        <Stack.Navigator
            screenOptions={{
                headerShown: false,
                animation: 'fade',
            }}
        >
            {!isAuthenticated ? (
                // Auth flow
                <Stack.Screen name="Login" component={LoginScreen} />
            ) : !user?.onboarding_completed ? (
                // Onboarding flow
                <Stack.Screen name="Onboarding" component={OnboardingScreen} />
            ) : (
                // Main app
                <Stack.Screen name="Home" component={HomeScreen} />
            )}
            {/* Shared Screens */}
            <Stack.Screen name="Vision" component={VisionRecordingScreen} />
        </Stack.Navigator>
    );
}

const styles = StyleSheet.create({
    loading: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#0A0A0A',
    },
});
