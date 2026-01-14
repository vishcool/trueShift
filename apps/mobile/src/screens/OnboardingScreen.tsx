/**
 * TrueShift - Onboarding Screen
 * 
 * Collects initial user preferences and permissions.
 */

import React, { useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    TouchableOpacity,
    ScrollView,
    TextInput,
} from 'react-native';

import { useAuth } from '../hooks/useAuth';
import { requestPermissionWithExplanation } from '../utils/permissions';

type OnboardingStep = 'welcome' | 'permissions' | 'consent' | 'goals';

const GOALS = ["Build Muscle", "Lose Weight", "Improve Stamina", "Flexibility"];
const EQUIPMENT = ["Full Gym", "Dumbbells Only", "Bodyweight", "Resistance Bands"];
const LEVELS = ["Beginner", "Intermediate", "Advanced"];

export function OnboardingScreen() {
    const { updateConsent, updateProfile } = useAuth();
    const [step, setStep] = useState<OnboardingStep>('welcome');
    const [isLoading, setIsLoading] = useState(false);

    // Profile Data
    const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
    const [selectedEquipment, setSelectedEquipment] = useState<string[]>([]);
    const [selectedLevel, setSelectedLevel] = useState<string>("Intermediate");

    // Consent Data
    const [consents, setConsents] = useState({
        location_tracking: false,
        health_data: false,
        camera_access: false,
        ai_coaching: false,
        data_analytics: false,
    });

    const handleNext = async () => {
        if (step === 'welcome') {
            setStep('permissions');
        } else if (step === 'permissions') {
            setStep('consent');
        } else if (step === 'consent') {
            await updateConsent(consents);
            setStep('goals');
        } else if (step === 'goals') {
            setIsLoading(true);
            try {
                // Save profile details and mark onboarding complete (handled by backend if goals present)
                await updateProfile({
                    fitness_goals: selectedGoals,
                    equipment: selectedEquipment,
                    fitness_level: selectedLevel,
                });
            } catch (e) {
                console.error("Failed to update profile", e);
            } finally {
                setIsLoading(false);
            }
        }
    };

    const toggleConsent = (key: keyof typeof consents) => {
        setConsents((prev) => ({ ...prev, [key]: !prev[key] }));
    };

    const toggleGoal = (goal: string) => {
        setSelectedGoals(prev =>
            prev.includes(goal) ? prev.filter(g => g !== goal) : [...prev, goal]
        );
    };

    const toggleEquipment = (eq: string) => {
        setSelectedEquipment(prev =>
            prev.includes(eq) ? prev.filter(e => e !== eq) : [...prev, eq]
        );
    };

    const requestPermission = async (type: 'location_foreground' | 'camera' | 'notifications') => {
        await requestPermissionWithExplanation(type);
    };

    return (
        <View style={styles.container}>
            <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
                {/* Welcome Step */}
                {step === 'welcome' && (
                    <View style={styles.stepContent}>
                        <Text style={styles.emoji}>🚀</Text>
                        <Text style={styles.title}>Welcome to TrueShift</Text>
                        <Text style={styles.description}>
                            Your AI-powered behavior intelligence engine that understands your
                            movement, environment, and recovery to optimize your performance.
                        </Text>
                    </View>
                )}

                {/* Permissions Step */}
                {step === 'permissions' && (
                    <View style={styles.stepContent}>
                        <Text style={styles.emoji}>🔐</Text>
                        <Text style={styles.title}>Enable Superpowers</Text>
                        <Text style={styles.description}>
                            TrueShift works best with access to your location and activity data.
                        </Text>

                        <View style={styles.permissionList}>
                            <TouchableOpacity
                                style={styles.permissionItem}
                                onPress={() => requestPermission('location_foreground')}
                            >
                                <Text style={styles.permissionIcon}>📍</Text>
                                <View style={styles.permissionText}>
                                    <Text style={styles.permissionTitle}>Location</Text>
                                    <Text style={styles.permissionDesc}>
                                        Context-aware recommendations
                                    </Text>
                                </View>
                            </TouchableOpacity>

                            <TouchableOpacity
                                style={styles.permissionItem}
                                onPress={() => requestPermission('notifications')}
                            >
                                <Text style={styles.permissionIcon}>🔔</Text>
                                <View style={styles.permissionText}>
                                    <Text style={styles.permissionTitle}>Notifications</Text>
                                    <Text style={styles.permissionDesc}>
                                        Timely coaching reminders
                                    </Text>
                                </View>
                            </TouchableOpacity>

                            <TouchableOpacity
                                style={styles.permissionItem}
                                onPress={() => requestPermission('camera')}
                            >
                                <Text style={styles.permissionIcon}>📷</Text>
                                <View style={styles.permissionText}>
                                    <Text style={styles.permissionTitle}>Camera</Text>
                                    <Text style={styles.permissionDesc}>
                                        Form analysis (optional)
                                    </Text>
                                </View>
                            </TouchableOpacity>
                        </View>
                    </View>
                )}

                {/* Consent Step */}
                {step === 'consent' && (
                    <View style={styles.stepContent}>
                        <Text style={styles.emoji}>✅</Text>
                        <Text style={styles.title}>Your Data, Your Choice</Text>
                        <Text style={styles.description}>
                            Choose what data you're comfortable sharing for personalized coaching.
                        </Text>

                        <View style={styles.consentList}>
                            {Object.entries({
                                location_tracking: ['📍', 'Location Tracking'],
                                health_data: ['❤️', 'Health Data'],
                                ai_coaching: ['🤖', 'AI Coaching'],
                                data_analytics: ['📊', 'Analytics'],
                            }).map(([key, [icon, label]]) => (
                                <TouchableOpacity
                                    key={key}
                                    style={[
                                        styles.consentItem,
                                        consents[key as keyof typeof consents] && styles.consentItemActive,
                                    ]}
                                    onPress={() => toggleConsent(key as keyof typeof consents)}
                                >
                                    <Text style={styles.consentIcon}>{icon}</Text>
                                    <Text style={styles.consentLabel}>{label}</Text>
                                    <View
                                        style={[
                                            styles.checkbox,
                                            consents[key as keyof typeof consents] && styles.checkboxActive,
                                        ]}
                                    />
                                </TouchableOpacity>
                            ))}
                        </View>
                    </View>
                )}

                {/* Goals Step */}
                {step === 'goals' && (
                    <View style={styles.stepContent}>
                        <Text style={styles.emoji}>🎯</Text>
                        <Text style={styles.title}>Your Profile</Text>
                        <Text style={styles.description}>
                            Help us tailor your workouts.
                        </Text>

                        <View style={styles.section}>
                            <Text style={styles.sectionTitle}>Fitness Level</Text>
                            <View style={styles.chipsContainer}>
                                {LEVELS.map(level => (
                                    <TouchableOpacity
                                        key={level}
                                        style={[styles.chip, selectedLevel === level && styles.chipActive]}
                                        onPress={() => setSelectedLevel(level)}
                                    >
                                        <Text style={[styles.chipText, selectedLevel === level && styles.chipTextActive]}>{level}</Text>
                                    </TouchableOpacity>
                                ))}
                            </View>
                        </View>

                        <View style={styles.section}>
                            <Text style={styles.sectionTitle}>Goals</Text>
                            <View style={styles.chipsContainer}>
                                {GOALS.map(goal => (
                                    <TouchableOpacity
                                        key={goal}
                                        style={[styles.chip, selectedGoals.includes(goal) && styles.chipActive]}
                                        onPress={() => toggleGoal(goal)}
                                    >
                                        <Text style={[styles.chipText, selectedGoals.includes(goal) && styles.chipTextActive]}>{goal}</Text>
                                    </TouchableOpacity>
                                ))}
                            </View>
                        </View>

                        <View style={styles.section}>
                            <Text style={styles.sectionTitle}>Equipment</Text>
                            <View style={styles.chipsContainer}>
                                {EQUIPMENT.map(eq => (
                                    <TouchableOpacity
                                        key={eq}
                                        style={[styles.chip, selectedEquipment.includes(eq) && styles.chipActive]}
                                        onPress={() => toggleEquipment(eq)}
                                    >
                                        <Text style={[styles.chipText, selectedEquipment.includes(eq) && styles.chipTextActive]}>{eq}</Text>
                                    </TouchableOpacity>
                                ))}
                            </View>
                        </View>

                    </View>
                )}
            </ScrollView>

            {/* Continue Button */}
            <View style={styles.footer}>
                <TouchableOpacity style={styles.continueButton} onPress={handleNext} disabled={isLoading}>
                    <Text style={styles.continueText}>
                        {isLoading ? "Saving..." : (step === 'goals' ? "Let's Go" : 'Continue')}
                    </Text>
                </TouchableOpacity>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0A0A0A',
    },
    content: {
        flex: 1,
    },
    scrollContent: {
        padding: 24,
        paddingTop: 80,
    },
    stepContent: {
        alignItems: 'center',
    },
    emoji: {
        fontSize: 64,
        marginBottom: 24,
    },
    title: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#FFFFFF',
        textAlign: 'center',
        marginBottom: 16,
    },
    description: {
        fontSize: 16,
        color: '#9CA3AF',
        textAlign: 'center',
        lineHeight: 24,
        maxWidth: 320,
    },
    section: {
        width: '100%',
        marginTop: 24,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: '600',
        color: '#DDD',
        marginBottom: 12,
    },
    chipsContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 8,
    },
    chip: {
        paddingVertical: 8,
        paddingHorizontal: 16,
        borderRadius: 20,
        backgroundColor: '#1F1F1F',
        borderWidth: 1,
        borderColor: '#333',
    },
    chipActive: {
        backgroundColor: '#4338ca', // Indigo 800
        borderColor: '#6366F1',
    },
    chipText: {
        color: '#AAA',
    },
    chipTextActive: {
        color: '#FFF',
        fontWeight: '600',
    },
    permissionList: {
        width: '100%',
        marginTop: 32,
        gap: 12,
    },
    permissionItem: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#1F1F1F',
        borderRadius: 12,
        padding: 16,
        gap: 16,
    },
    permissionIcon: {
        fontSize: 24,
    },
    permissionText: {
        flex: 1,
    },
    permissionTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#FFFFFF',
    },
    permissionDesc: {
        fontSize: 14,
        color: '#9CA3AF',
        marginTop: 2,
    },
    consentList: {
        width: '100%',
        marginTop: 32,
        gap: 12,
    },
    consentItem: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#1F1F1F',
        borderRadius: 12,
        padding: 16,
        gap: 16,
    },
    consentItemActive: {
        borderColor: '#6366F1',
        borderWidth: 1,
    },
    consentIcon: {
        fontSize: 24,
    },
    consentLabel: {
        flex: 1,
        fontSize: 16,
        color: '#FFFFFF',
    },
    checkbox: {
        width: 24,
        height: 24,
        borderRadius: 6,
        borderWidth: 2,
        borderColor: '#4B5563',
    },
    checkboxActive: {
        backgroundColor: '#6366F1',
        borderColor: '#6366F1',
    },
    footer: {
        padding: 24,
        paddingBottom: 40,
    },
    continueButton: {
        backgroundColor: '#6366F1',
        borderRadius: 12,
        paddingVertical: 16,
        alignItems: 'center',
    },
    continueText: {
        fontSize: 16,
        fontWeight: '600',
        color: '#FFFFFF',
    },
});
