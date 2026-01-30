import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, Alert, KeyboardAvoidingView, Platform } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { api } from '../api/client';

export default function ActiveSessionScreen() {
    const navigation = useNavigation<any>();
    const route = useRoute<any>();
    const { exercises } = route.params || { exercises: [] };

    // Track input for each exercise
    // Structure: { [exerciseIndex]: [ { weight: '20', reps: '10' }, ... ] }
    const [logs, setLogs] = useState<any>({});
    const [submitting, setSubmitting] = useState(false);

    const updateLog = (exerciseIdx: number, setIdx: number, field: 'weight' | 'reps', value: string) => {
        const currentExLogs = logs[exerciseIdx] || [];
        // Ensure array size
        const newExLogs = [...currentExLogs];
        if (!newExLogs[setIdx]) newExLogs[setIdx] = { weight: '', reps: '' };

        newExLogs[setIdx] = { ...newExLogs[setIdx], [field]: value };

        setLogs({ ...logs, [exerciseIdx]: newExLogs });
    };

    const finishWorkout = async () => {
        setSubmitting(true);
        try {
            // Construct payload for backend
            const workoutData = {
                exercises: exercises.map((ex: any, idx: number) => ({
                    name: ex.name,
                    sets: logs[idx] || []
                })),
                completed_at: new Date().toISOString()
            };

            // Call API (assuming we have a log endpoint or update the existing plan)
            // await api.workout.log(workoutData);
            await api.workout.record(workoutData);

            Alert.alert("Great Job!", "Workout saved successfully.", [
                { text: "OK", onPress: () => navigation.navigate('Profile') }
            ]);
        } catch (e) {
            Alert.alert("Error", "Failed to save workout.");
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <KeyboardAvoidingView
            behavior={Platform.OS === "ios" ? "padding" : "height"}
            style={styles.container}
        >
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()} style={styles.closeBtn}>
                    <Text style={styles.closeText}>Quit</Text>
                </TouchableOpacity>
                <Text style={styles.timer}>00:00</Text>
                <TouchableOpacity onPress={finishWorkout} disabled={submitting}>
                    <Text style={styles.finishText}>Finish</Text>
                </TouchableOpacity>
            </View>

            <ScrollView style={styles.content}>
                {exercises.map((ex: any, idx: number) => (
                    <View key={idx} style={styles.exerciseCard}>
                        <Text style={styles.exerciseName}>{ex.name}</Text>
                        <Text style={styles.targetText}>Target: {ex.sets} sets × {ex.reps}</Text>

                        {/* Render Set Inputs */}
                        {Array.from({ length: ex.sets }).map((_, setIdx) => (
                            <View key={setIdx} style={styles.setRow}>
                                <Text style={styles.setLabel}>Set {setIdx + 1}</Text>
                                <TextInput
                                    style={styles.input}
                                    placeholder="kg"
                                    placeholderTextColor="#555"
                                    keyboardType="numeric"
                                    onChangeText={(v) => updateLog(idx, setIdx, 'weight', v)}
                                />
                                <TextInput
                                    style={styles.input}
                                    placeholder="reps"
                                    placeholderTextColor="#555"
                                    keyboardType="numeric"
                                    onChangeText={(v) => updateLog(idx, setIdx, 'reps', v)}
                                />
                            </View>
                        ))}
                    </View>
                ))}
                <View style={{ height: 100 }} />
            </ScrollView>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0A0A0A',
    },
    header: {
        paddingTop: 60,
        paddingHorizontal: 20,
        paddingBottom: 20,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottomWidth: 1,
        borderBottomColor: '#222',
    },
    closeBtn: {},
    closeText: { color: '#EF4444', fontSize: 16 },
    timer: { color: 'white', fontSize: 18, fontWeight: 'bold' },
    finishText: { color: '#10B981', fontSize: 16, fontWeight: 'bold' },
    content: {
        padding: 20,
    },
    exerciseCard: {
        backgroundColor: '#1F1F1F',
        borderRadius: 12,
        padding: 16,
        marginBottom: 20,
    },
    exerciseName: {
        color: 'white',
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 4,
    },
    targetText: {
        color: '#999',
        fontSize: 14,
        marginBottom: 16,
    },
    setRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 12,
        gap: 12,
    },
    setLabel: {
        color: '#666',
        width: 40,
    },
    input: {
        flex: 1,
        backgroundColor: '#111',
        borderWidth: 1,
        borderColor: '#333',
        borderRadius: 8,
        padding: 12,
        color: 'white',
        textAlign: 'center',
    },
});
