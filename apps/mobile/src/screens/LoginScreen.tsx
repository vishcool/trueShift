/**
 * TrueShift - Login Screen
 * 
 * Placeholder login screen for Firebase authentication.
 */

import React, { useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    TouchableOpacity,
    TextInput,
    ActivityIndicator,
} from 'react-native';

import { useAuth } from '../hooks/useAuth';

export function LoginScreen() {
    const { login } = useAuth();
    const [isLoading, setIsLoading] = useState(false);

    // In production, this would use Firebase Auth UI
    const handleLogin = async () => {
        setIsLoading(true);
        try {
            // Placeholder: In production, get token from Firebase
            // const credential = await signInWithGoogle();
            // await login(credential.idToken);

            // For dev, use a mock token
            await login('dev-token-placeholder');
        } catch (error) {
            console.error('Login failed:', error);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <View style={styles.container}>
            {/* Logo/Brand */}
            <View style={styles.header}>
                <Text style={styles.logo}>TrueShift</Text>
                <Text style={styles.tagline}>
                    Your AI-powered behavior intelligence engine
                </Text>
            </View>

            {/* Login Options */}
            <View style={styles.loginSection}>
                <TouchableOpacity
                    style={styles.googleButton}
                    onPress={handleLogin}
                    disabled={isLoading}
                >
                    {isLoading ? (
                        <ActivityIndicator color="#000" />
                    ) : (
                        <Text style={styles.googleButtonText}>Continue with Google</Text>
                    )}
                </TouchableOpacity>

                <TouchableOpacity
                    style={styles.appleButton}
                    onPress={handleLogin}
                    disabled={isLoading}
                >
                    <Text style={styles.appleButtonText}>Continue with Apple</Text>
                </TouchableOpacity>
            </View>

            {/* Footer */}
            <View style={styles.footer}>
                <Text style={styles.footerText}>
                    By continuing, you agree to our Terms of Service and Privacy Policy
                </Text>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0A0A0A',
        justifyContent: 'space-between',
        paddingHorizontal: 24,
        paddingVertical: 60,
    },
    header: {
        alignItems: 'center',
        marginTop: 80,
    },
    logo: {
        fontSize: 42,
        fontWeight: 'bold',
        color: '#FFFFFF',
        letterSpacing: -1,
    },
    tagline: {
        fontSize: 16,
        color: '#9CA3AF',
        textAlign: 'center',
        marginTop: 12,
        maxWidth: 280,
    },
    loginSection: {
        gap: 16,
    },
    googleButton: {
        backgroundColor: '#FFFFFF',
        borderRadius: 12,
        paddingVertical: 16,
        alignItems: 'center',
    },
    googleButtonText: {
        fontSize: 16,
        fontWeight: '600',
        color: '#000000',
    },
    appleButton: {
        backgroundColor: '#1F1F1F',
        borderRadius: 12,
        paddingVertical: 16,
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#333',
    },
    appleButtonText: {
        fontSize: 16,
        fontWeight: '600',
        color: '#FFFFFF',
    },
    footer: {
        alignItems: 'center',
    },
    footerText: {
        fontSize: 12,
        color: '#6B7280',
        textAlign: 'center',
        lineHeight: 18,
    },
});
