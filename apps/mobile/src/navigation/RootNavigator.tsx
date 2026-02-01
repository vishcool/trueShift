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
import { WorkoutGenScreen } from '../screens/WorkoutGenScreen';
import VisionRecordingScreen from '../screens/VisionRecordingScreen';
import ScanEquipmentScreen from '../screens/ScanEquipmentScreen';
import ExerciseSelectionScreen from '../screens/ExerciseSelectionScreen';
import ProfileScreen from '../screens/ProfileScreen';
import ActiveSessionScreen from '../screens/ActiveSessionScreen';
import ChatScreen from '../screens/ChatScreen';

export type RootStackParamList = {
    Login: undefined;
    Onboarding: undefined;
    Home: undefined;
    Chat: undefined;
    Vision: { planId?: string; exercises?: any[] } | undefined;
    WorkoutGen: { generatedPlan?: any } | undefined;
    ScanEquipment: undefined;
    ExerciseSelection: { suggestions: any[]; analysis?: string };
    Profile: { addedExercises?: any[] } | undefined;
    ActiveSession: { exercises: any[] };
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
            <Stack.Screen name="WorkoutGen" component={WorkoutGenScreen} />
            <Stack.Screen name="Vision" component={VisionRecordingScreen} />
            <Stack.Screen name="ScanEquipment" component={ScanEquipmentScreen} />
            <Stack.Screen name="ExerciseSelection" component={ExerciseSelectionScreen} />
            <Stack.Screen name="Profile" component={ProfileScreen} />
            <Stack.Screen name="ActiveSession" component={ActiveSessionScreen} />
            <Stack.Screen name="Chat" component={ChatScreen} />
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
