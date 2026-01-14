/**
 * TrueShift - Workout Generation Screen
 * 
 * Generates and displays a personalized workout plan.
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { api, WorkoutPlanResponse, WorkoutGenerationRequest } from '../api/client';
import { useAuth } from '../hooks/useAuth';

export function WorkoutGenScreen() {
    const navigation = useNavigation<any>();
    const { user } = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [workoutPlan, setWorkoutPlan] = useState<WorkoutPlanResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const generateWorkout = async () => {
        setIsLoading(true);
        setError(null);
        try {
            // Use profile data for generation
            // In a real app, we might ask for specific focus for *today*
            // For now, we use defaults or user preferences
            const request: WorkoutGenerationRequest = {
                duration_minutes: 45,
                fitness_level: "Intermediate", // could fetch from profile
                // equipment and goals are implicitly handled by backend for now if null, 
                // or we can explicitly pass them if we stored them in user.preferences locally
            };

            const response = await api.workout.generate(request);
            setWorkoutPlan(response.data);
        } catch (e) {
            console.error(e);
            setError("Failed to generate workout. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    const startWorkout = () => {
        if (workoutPlan) {
            // Navigate to tracking/vision screen
            // We pass the first exercise or the whole plan
            navigation.navigate('Vision', {
                planId: workoutPlan.id,
                exercises: workoutPlan.plan_data.exercises
            });
        }
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.headerTitle}>Todays Session</Text>
            </View>

            <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
                {!workoutPlan && !isLoading && (
                    <View style={styles.placeholder}>
                        <Text style={styles.placeholderText}>
                            Ready to train? Let AI build your perfect session based on your recovery and goals.
                        </Text>
                        <TouchableOpacity style={styles.generateButton} onPress={generateWorkout}>
                            <Text style={styles.buttonText}>Generate Workout</Text>
                        </TouchableOpacity>
                    </View>
                )}

                {isLoading && (
                    <View style={styles.loading}>
                        <ActivityIndicator size="large" color="#6366F1" />
                        <Text style={styles.loadingText}>Analyzing recovery & designing session...</Text>
                    </View>
                )}

                {error && (
                    <View style={styles.error}>
                        <Text style={styles.errorText}>{error}</Text>
                        <TouchableOpacity style={styles.retryButton} onPress={generateWorkout}>
                            <Text style={styles.buttonText}>Retry</Text>
                        </TouchableOpacity>
                    </View>
                )}

                {workoutPlan && (
                    <View style={styles.planContainer}>
                        <Text style={styles.planTitle}>{workoutPlan.plan_data.overview}</Text>

                        <View style={styles.exerciseList}>
                            {workoutPlan.plan_data.exercises.map((ex, idx) => (
                                <View key={idx} style={styles.exerciseCard}>
                                    <View style={styles.exerciseHeader}>
                                        <Text style={styles.exerciseName}>{ex.name}</Text>
                                        <Text style={styles.exerciseMeta}>{ex.sets} sets × {ex.reps}</Text>
                                    </View>
                                    {ex.notes && <Text style={styles.exerciseNotes}>{ex.notes}</Text>}
                                </View>
                            ))}
                        </View>
                    </View>
                )}
            </ScrollView>

            {workoutPlan && (
                <View style={styles.footer}>
                    <TouchableOpacity style={styles.startButton} onPress={startWorkout}>
                        <Text style={styles.startButtonText}>Start Workout</Text>
                    </TouchableOpacity>
                </View>
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0A0A0A',
    },
    header: {
        paddingTop: 60,
        paddingBottom: 20,
        paddingHorizontal: 24,
        borderBottomWidth: 1,
        borderBottomColor: '#1F1F1F',
    },
    headerTitle: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#FFF',
    },
    content: {
        flex: 1,
    },
    scrollContent: {
        padding: 24,
        paddingBottom: 100,
    },
    placeholder: {
        alignItems: 'center',
        paddingVertical: 40,
    },
    placeholderText: {
        color: '#9CA3AF',
        textAlign: 'center',
        fontSize: 16,
        marginBottom: 32,
        lineHeight: 24,
    },
    generateButton: {
        backgroundColor: '#6366F1',
        paddingHorizontal: 32,
        paddingVertical: 16,
        borderRadius: 12,
        width: '100%',
        alignItems: 'center',
    },
    buttonText: {
        color: '#FFF',
        fontWeight: '600',
        fontSize: 16,
    },
    loading: {
        alignItems: 'center',
        paddingVertical: 40,
    },
    loadingText: {
        color: '#9CA3AF',
        marginTop: 16,
    },
    error: {
        alignItems: 'center',
        paddingVertical: 20,
    },
    errorText: {
        color: '#EF4444',
        marginBottom: 16,
        textAlign: 'center',
    },
    retryButton: {
        backgroundColor: '#374151',
        paddingHorizontal: 24,
        paddingVertical: 12,
        borderRadius: 8,
    },
    planContainer: {
        gap: 24,
    },
    planTitle: {
        fontSize: 20,
        fontWeight: '600',
        color: '#E0E7FF',
    },
    exerciseList: {
        gap: 16,
    },
    exerciseCard: {
        backgroundColor: '#1F1F1F',
        borderRadius: 12,
        padding: 16,
        borderLeftWidth: 4,
        borderLeftColor: '#6366F1',
    },
    exerciseHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 8,
    },
    exerciseName: {
        fontSize: 18,
        fontWeight: '600',
        color: '#FFF',
    },
    exerciseMeta: {
        color: '#A5B4FC',
        fontSize: 14,
        fontWeight: '500',
    },
    exerciseNotes: {
        color: '#9CA3AF',
        fontSize: 14,
        fontStyle: 'italic',
    },
    footer: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        padding: 24,
        backgroundColor: 'rgba(10,10,10,0.9)',
    },
    startButton: {
        backgroundColor: '#10B981', // Emerald 500
        paddingVertical: 18,
        borderRadius: 12,
        alignItems: 'center',
    },
    startButtonText: {
        color: '#FFF',
        fontSize: 18,
        fontWeight: 'bold',
    },
});
