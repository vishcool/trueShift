/**
 * TrueShift Mobile App Entry Point
 * 
 * This is the main entry point for the TrueShift mobile application.
 * Configures navigation, state management, and background services.
 */

import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { RootNavigator } from './src/navigation/RootNavigator';
import { initBackgroundServices } from './src/services/BackgroundSync';
import { useAuthStore } from './src/store/authStore';

// Initialize React Query client
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 60 * 5, // 5 minutes
            retry: 2,
        },
    },
});

export default function App() {
    const { initialize } = useAuthStore();

    useEffect(() => {
        // Initialize auth state
        initialize();

        // Initialize background services
        initBackgroundServices();
    }, []);

    return (
        <QueryClientProvider client={queryClient}>
            <SafeAreaProvider>
                <NavigationContainer>
                    <StatusBar style="light" />
                    <RootNavigator />
                </NavigationContainer>
            </SafeAreaProvider>
        </QueryClientProvider>
    );
}
