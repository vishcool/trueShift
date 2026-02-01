/**
 * TrueShift - Workout Generation Screen
 * 
 * Comprehensive workout planner with conversational AI agent.
 */

import React, { useState, useRef, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    TouchableOpacity,
    ScrollView,
    ActivityIndicator,
    TextInput,
    KeyboardAvoidingView,
    Platform,
    FlatList
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { api } from '../api/client';
import { useAuth } from '../hooks/useAuth';

interface Message {
    id: string;
    text: string;
    sender: 'user' | 'agent';
    timestamp: Date;
}

interface WorkoutPlan {
    id: string;
    plan_data: {
        overview: string;
        exercises: Array<{
            name: string;
            sets: number | string;
            reps: number | string;
            rest_seconds?: number;
            notes?: string;
        }>;
    };
}

const EQUIPMENT_OPTIONS = [
    'Dumbbells',
    'Barbell',
    'Resistance Bands',
    'Bodyweight',
    'Kettlebell',
    'Pull-up Bar',
    'Bench',
];

const TIME_OPTIONS = [15, 30, 45, 60];

export function WorkoutGenScreen() {
    const navigation = useNavigation<any>();
    const route = useRoute<any>();
    const { user } = useAuth();
    const scrollViewRef = useRef<ScrollView>(null);
    const chatScrollRef = useRef<FlatList>(null);

    const [isLoading, setIsLoading] = useState(false);
    const [workoutPlan, setWorkoutPlan] = useState<WorkoutPlan | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Chat state
    const [messages, setMessages] = useState<Message[]>([]);
    const [inputText, setInputText] = useState('');
    const [isChatLoading, setIsChatLoading] = useState(false);

    // Preferences
    const [selectedEquipment, setSelectedEquipment] = useState<string[]>(['Bodyweight']);
    const [selectedTime, setSelectedTime] = useState(30);

    useEffect(() => {
        if (route.params?.generatedPlan) {
            setWorkoutPlan(route.params.generatedPlan);
        }

        // Initial greeting
        setMessages([{
            id: '1',
            text: `Hi ${user?.display_name || 'there'}! I'm your AI workout coach. Tell me what you'd like to work on today, or I can generate a plan based on your equipment and time.`,
            sender: 'agent',
            timestamp: new Date(),
        }]);
    }, [route.params?.generatedPlan]);

    const toggleEquipment = (equipment: string) => {
        setSelectedEquipment(prev =>
            prev.includes(equipment)
                ? prev.filter(e => e !== equipment)
                : [...prev, equipment]
        );
    };

    const generateWorkout = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await api.workout.generate({
                duration_minutes: selectedTime,
                equipment: selectedEquipment,
                fitness_level: 'Intermediate',
            });
            setWorkoutPlan(response.data);

            // Add agent message
            const agentMsg: Message = {
                id: Date.now().toString(),
                text: `I've created a ${selectedTime}-minute workout for you! Check it out below. Feel free to ask me to adjust anything.`,
                sender: 'agent',
                timestamp: new Date(),
            };
            setMessages(prev => [...prev, agentMsg]);
        } catch (e) {
            console.error(e);
            setError("Failed to generate workout. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    const sendMessage = async () => {
        if (!inputText.trim()) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            text: inputText,
            sender: 'user',
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMsg]);
        setInputText('');
        setIsChatLoading(true);

        try {
            const context = {
                current_plan: workoutPlan,
                equipment: selectedEquipment,
                time: selectedTime,
            };

            const response = await api.agent.chat(userMsg.text, context);

            const agentMsg: Message = {
                id: (Date.now() + 1).toString(),
                text: response.data.response,
                sender: 'agent',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, agentMsg]);

            // If the agent's response suggests a new workout, regenerate
            if (response.data.response.toLowerCase().includes('generated') ||
                response.data.response.toLowerCase().includes('updated')) {
                await generateWorkout();
            }
        } catch (error) {
            const errorMsg: Message = {
                id: (Date.now() + 1).toString(),
                text: "Sorry, I'm having trouble right now. Please try again.",
                sender: 'agent',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMsg]);
        } finally {
            setIsChatLoading(false);
        }
    };

    const startWorkout = () => {
        if (workoutPlan) {
            navigation.navigate('ActiveSession', {
                exercises: workoutPlan.plan_data.exercises
            });
        }
    };

    const scanEquipment = () => {
        navigation.navigate('ScanEquipment');
    };

    return (
        <KeyboardAvoidingView
            style={styles.container}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            keyboardVerticalOffset={0}
        >
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()}>
                    <Text style={styles.backButton}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Workout Planner</Text>
                <View style={{ width: 60 }} />
            </View>

            <ScrollView
                ref={scrollViewRef}
                style={styles.content}
                contentContainerStyle={styles.scrollContent}
            >
                {/* Equipment Selection */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Available Equipment</Text>
                    <View style={styles.chipContainer}>
                        {EQUIPMENT_OPTIONS.map(equipment => (
                            <TouchableOpacity
                                key={equipment}
                                style={[
                                    styles.chip,
                                    selectedEquipment.includes(equipment) && styles.chipSelected
                                ]}
                                onPress={() => toggleEquipment(equipment)}
                            >
                                <Text style={[
                                    styles.chipText,
                                    selectedEquipment.includes(equipment) && styles.chipTextSelected
                                ]}>
                                    {equipment}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                    <TouchableOpacity style={styles.scanLink} onPress={scanEquipment}>
                        <Text style={styles.scanLinkText}>📷 Scan Equipment</Text>
                    </TouchableOpacity>
                </View>

                {/* Time Selection */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Workout Duration</Text>
                    <View style={styles.chipContainer}>
                        {TIME_OPTIONS.map(time => (
                            <TouchableOpacity
                                key={time}
                                style={[
                                    styles.chip,
                                    selectedTime === time && styles.chipSelected
                                ]}
                                onPress={() => setSelectedTime(time)}
                            >
                                <Text style={[
                                    styles.chipText,
                                    selectedTime === time && styles.chipTextSelected
                                ]}>
                                    {time} min
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                </View>

                {/* Generate Button */}
                {!workoutPlan && !isLoading && (
                    <TouchableOpacity style={styles.generateButton} onPress={generateWorkout}>
                        <Text style={styles.generateButtonText}>Generate Workout Plan</Text>
                    </TouchableOpacity>
                )}

                {/* Loading */}
                {isLoading && (
                    <View style={styles.loading}>
                        <ActivityIndicator size="large" color="#6366F1" />
                        <Text style={styles.loadingText}>Creating your perfect workout...</Text>
                    </View>
                )}

                {/* Error */}
                {error && (
                    <View style={styles.error}>
                        <Text style={styles.errorText}>{error}</Text>
                        <TouchableOpacity style={styles.retryButton} onPress={generateWorkout}>
                            <Text style={styles.buttonText}>Retry</Text>
                        </TouchableOpacity>
                    </View>
                )}

                {/* Workout Plan */}
                {workoutPlan && (
                    <View style={styles.planContainer}>
                        <Text style={styles.planTitle}>{workoutPlan.plan_data.overview}</Text>

                        <View style={styles.exerciseList}>
                            {workoutPlan.plan_data.exercises.map((ex, idx) => (
                                <View key={idx} style={styles.exerciseCard}>
                                    <View style={styles.exerciseHeader}>
                                        <Text style={styles.exerciseName}>{ex.name}</Text>
                                        <Text style={styles.exerciseMeta}>{ex.sets} × {ex.reps}</Text>
                                    </View>
                                    {ex.notes && <Text style={styles.exerciseNotes}>{ex.notes}</Text>}
                                </View>
                            ))}
                        </View>
                    </View>
                )}

                {/* Chat Messages */}
                <View style={styles.chatSection}>
                    <Text style={styles.sectionTitle}>Chat with Coach</Text>
                    <View style={styles.chatMessages}>
                        {messages.map(msg => (
                            <View
                                key={msg.id}
                                style={[
                                    styles.messageBubble,
                                    msg.sender === 'user' ? styles.userBubble : styles.agentBubble
                                ]}
                            >
                                <Text style={styles.messageText}>{msg.text}</Text>
                                <Text style={styles.timestamp}>
                                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </Text>
                            </View>
                        ))}
                    </View>
                </View>

                <View style={{ height: 180 }} />
            </ScrollView>

            {/* Chat Input */}
            <View style={styles.chatInputContainer}>
                <TextInput
                    style={styles.chatInput}
                    value={inputText}
                    onChangeText={setInputText}
                    placeholder="Ask to modify workout, change exercises..."
                    placeholderTextColor="#666"
                    onSubmitEditing={sendMessage}
                    multiline
                />
                <TouchableOpacity
                    style={[styles.sendButton, (!inputText.trim() || isChatLoading) && styles.sendButtonDisabled]}
                    onPress={sendMessage}
                    disabled={!inputText.trim() || isChatLoading}
                >
                    {isChatLoading ? (
                        <ActivityIndicator color="white" size="small" />
                    ) : (
                        <Text style={styles.sendButtonText}>Send</Text>
                    )}
                </TouchableOpacity>
            </View>

            {/* Start Workout Button */}
            {workoutPlan && (
                <View style={styles.footer}>
                    <TouchableOpacity style={styles.startButton} onPress={startWorkout}>
                        <Text style={styles.startButtonText}>Start Workout</Text>
                    </TouchableOpacity>
                </View>
            )}
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0A0A0A',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingTop: 60,
        paddingBottom: 16,
        paddingHorizontal: 20,
        borderBottomWidth: 1,
        borderBottomColor: '#1F1F1F',
    },
    backButton: {
        color: '#6366F1',
        fontSize: 16,
    },
    headerTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#FFF',
    },
    content: {
        flex: 1,
    },
    scrollContent: {
        padding: 20,
    },
    section: {
        marginBottom: 24,
    },
    sectionTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#FFF',
        marginBottom: 12,
    },
    chipContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 8,
    },
    chip: {
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 20,
        backgroundColor: '#1F1F1F',
        borderWidth: 1,
        borderColor: '#333',
    },
    chipSelected: {
        backgroundColor: '#6366F1',
        borderColor: '#6366F1',
    },
    chipText: {
        color: '#9CA3AF',
        fontSize: 14,
        fontWeight: '500',
    },
    chipTextSelected: {
        color: '#FFF',
    },
    scanLink: {
        marginTop: 12,
    },
    scanLinkText: {
        color: '#6366F1',
        fontSize: 14,
    },
    generateButton: {
        backgroundColor: '#6366F1',
        paddingVertical: 16,
        borderRadius: 12,
        alignItems: 'center',
        marginBottom: 24,
    },
    generateButtonText: {
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
    buttonText: {
        color: '#FFF',
        fontWeight: '600',
    },
    planContainer: {
        marginBottom: 24,
    },
    planTitle: {
        fontSize: 18,
        fontWeight: '600',
        color: '#E0E7FF',
        marginBottom: 16,
    },
    exerciseList: {
        gap: 12,
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
        marginBottom: 4,
    },
    exerciseName: {
        fontSize: 16,
        fontWeight: '600',
        color: '#FFF',
        flex: 1,
    },
    exerciseMeta: {
        color: '#A5B4FC',
        fontSize: 14,
        fontWeight: '500',
    },
    exerciseNotes: {
        color: '#9CA3AF',
        fontSize: 13,
        fontStyle: 'italic',
        marginTop: 4,
    },
    chatSection: {
        marginBottom: 24,
    },
    chatMessages: {
        gap: 12,
    },
    messageBubble: {
        maxWidth: '85%',
        padding: 12,
        borderRadius: 16,
    },
    userBubble: {
        backgroundColor: '#6366F1',
        alignSelf: 'flex-end',
        borderBottomRightRadius: 4,
    },
    agentBubble: {
        backgroundColor: '#1F1F1F',
        alignSelf: 'flex-start',
        borderBottomLeftRadius: 4,
    },
    messageText: {
        color: '#FFFFFF',
        fontSize: 15,
        lineHeight: 20,
    },
    timestamp: {
        color: 'rgba(255,255,255,0.5)',
        fontSize: 10,
        marginTop: 4,
        alignSelf: 'flex-end',
    },
    chatInputContainer: {
        flexDirection: 'row',
        padding: 16,
        borderTopWidth: 1,
        borderTopColor: '#222',
        backgroundColor: '#0A0A0A',
        gap: 12,
    },
    chatInput: {
        flex: 1,
        backgroundColor: '#1F1F1F',
        borderRadius: 20,
        paddingHorizontal: 16,
        paddingVertical: 10,
        color: '#FFFFFF',
        fontSize: 15,
        maxHeight: 100,
    },
    sendButton: {
        backgroundColor: '#6366F1',
        width: 48,
        height: 48,
        borderRadius: 24,
        justifyContent: 'center',
        alignItems: 'center',
    },
    sendButtonDisabled: {
        opacity: 0.5,
    },
    sendButtonText: {
        color: '#FFFFFF',
        fontWeight: 'bold',
        fontSize: 12,
    },
    footer: {
        padding: 16,
        backgroundColor: 'rgba(10,10,10,0.95)',
        borderTopWidth: 1,
        borderTopColor: '#222',
    },
    startButton: {
        backgroundColor: '#10B981',
        paddingVertical: 16,
        borderRadius: 12,
        alignItems: 'center',
    },
    startButtonText: {
        color: '#FFF',
        fontSize: 16,
        fontWeight: 'bold',
    },
});
