import React, { useEffect, useMemo, useState } from 'react';
import {
    Alert,
    KeyboardAvoidingView,
    Platform,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';

import { api, WorkoutRecordedExercise } from '../api/client';
import { SurfaceCard } from '../components/ui/SurfaceCard';
import { useWorkoutSessionStore } from '../store/workoutSessionStore';
import { trackEvent } from '../services/BackgroundSync';

interface SetLog {
    weight: string;
    reps: string;
}

export default function ActiveSessionScreen() {
    const navigation = useNavigation<any>();
    const route = useRoute<any>();
    const { exercises } = route.params || { exercises: [] };

    const [submitting, setSubmitting] = useState(false);
    const [sessionStart] = useState(Date.now());
    const {
        logs,
        sessionId,
        initializeSession,
        updateLog: updateWorkoutLog,
        currentExerciseIndex,
        clearSession,
    } = useWorkoutSessionStore();

    const estimatedDuration = useMemo(() => {
        const mins = Math.round((Date.now() - sessionStart) / 60000);
        return Math.max(mins, 1);
    }, [sessionStart]);

    useEffect(() => {
        initializeSession(exercises);
    }, [exercises, initializeSession]);

    useEffect(() => {
        if (!sessionId) {
            return;
        }
        trackEvent('workout.started', {
            session_id: sessionId,
            workout_type: 'guided_session',
            planned_exercise_count: exercises.length,
        }).catch(() => undefined);
    }, [exercises.length, sessionId]);

    const updateLog = (exerciseIdx: number, setIdx: number, field: 'weight' | 'reps', value: string) => {
        updateWorkoutLog(exerciseIdx, setIdx, field, value);
    };

    const finishWorkout = async () => {
        setSubmitting(true);
        try {
            const workoutData = {
                exercises: exercises.map((ex: any, idx: number): WorkoutRecordedExercise => ({
                    name: ex.name,
                    target_sets: ex.sets,
                    target_reps: ex.reps,
                    performed_sets: (logs[idx] || []).map((setLog, setIndex) => ({
                        set_number: setIndex + 1,
                        weight: setLog.weight,
                        reps: setLog.reps,
                        completed_at: new Date().toISOString(),
                    })),
                })),
                duration_minutes: estimatedDuration,
                completed_at: new Date().toISOString(),
                session_id: sessionId || undefined,
            };

            await api.workout.record(workoutData);
            await trackEvent('workout.completed', {
                session_id: sessionId,
                workout_type: 'guided_session',
                duration_minutes: estimatedDuration,
                exercise_count: exercises.length,
            });

            Alert.alert('Great Job!', 'Workout saved successfully.', [
                {
                    text: 'OK',
                    onPress: () => {
                        clearSession();
                        navigation.navigate('Profile');
                    },
                },
            ]);
        } catch {
            Alert.alert('Error', 'Failed to save workout. Please try again.');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.container}
        >
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()}>
                    <Text style={styles.closeText}>Quit</Text>
                </TouchableOpacity>
                <Text style={styles.timer}>{estimatedDuration} min</Text>
                <View style={styles.headerActions}>
                    <TouchableOpacity onPress={() => navigation.navigate('VoiceCoach', { initialMode: 'workout', activeWorkout: true })}>
                        <Text style={styles.voiceText}>Coach</Text>
                    </TouchableOpacity>
                    <TouchableOpacity onPress={finishWorkout} disabled={submitting}>
                        <Text style={styles.finishText}>{submitting ? 'Saving...' : 'Finish'}</Text>
                    </TouchableOpacity>
                </View>
            </View>

            <ScrollView style={styles.content} contentContainerStyle={styles.contentContainer}>
                {exercises.map((ex: any, idx: number) => (
                    <SurfaceCard
                        key={idx}
                        style={idx === currentExerciseIndex ? { ...styles.exerciseCard, ...styles.exerciseCardActive } : styles.exerciseCard}
                    >
                        <Text style={styles.exerciseName}>{ex.name}</Text>
                        <Text style={styles.targetText}>Target: {ex.sets} sets x {ex.reps}</Text>

                        {Array.from({ length: Number(ex.sets) || 1 }).map((_, setIdx) => (
                            <View key={setIdx} style={styles.setRow}>
                                <Text style={styles.setLabel}>Set {setIdx + 1}</Text>
                                <TextInput
                                    style={styles.input}
                                    placeholder="kg"
                                    placeholderTextColor="#6B7280"
                                    keyboardType="numeric"
                                    value={logs[idx]?.[setIdx]?.weight || ''}
                                    onChangeText={(v) => updateLog(idx, setIdx, 'weight', v)}
                                />
                                <TextInput
                                    style={styles.input}
                                    placeholder="reps"
                                    placeholderTextColor="#6B7280"
                                    keyboardType="numeric"
                                    value={logs[idx]?.[setIdx]?.reps || ''}
                                    onChangeText={(v) => updateLog(idx, setIdx, 'reps', v)}
                                />
                            </View>
                        ))}
                    </SurfaceCard>
                ))}
                <View style={{ height: 24 }} />
            </ScrollView>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#050505',
    },
    header: {
        paddingTop: 58,
        paddingHorizontal: 16,
        paddingBottom: 14,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottomWidth: 1,
        borderBottomColor: '#222222',
    },
    closeText: { color: '#F87171', fontSize: 16 },
    timer: { color: '#F3F4F6', fontSize: 18, fontWeight: '700' },
    finishText: { color: '#93C5FD', fontSize: 16, fontWeight: '700' },
    voiceText: { color: '#FCD34D', fontSize: 16, fontWeight: '700' },
    headerActions: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 14,
    },
    content: {
        flex: 1,
    },
    contentContainer: {
        padding: 16,
    },
    exerciseCard: {
        padding: 14,
        marginBottom: 14,
    },
    exerciseCardActive: {
        borderWidth: 1,
        borderColor: '#F59E0B',
    },
    exerciseName: {
        color: '#FFFFFF',
        fontSize: 18,
        fontWeight: '700',
        marginBottom: 4,
    },
    targetText: {
        color: '#9CA3AF',
        fontSize: 14,
        marginBottom: 12,
    },
    setRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 10,
        gap: 10,
    },
    setLabel: {
        color: '#9CA3AF',
        width: 46,
        fontSize: 13,
    },
    input: {
        flex: 1,
        backgroundColor: '#0F0F0F',
        borderWidth: 1,
        borderColor: '#2F2F2F',
        borderRadius: 10,
        padding: 11,
        color: '#F3F4F6',
        textAlign: 'center',
        fontSize: 14,
    },
});
