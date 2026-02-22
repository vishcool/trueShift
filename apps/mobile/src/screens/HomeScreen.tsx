/**
 * TrueShift - Home Screen
 * 
 * Chat-centric dashboard with AI coach for workouts, equipment scanning,
 * and workout generation.
 */

import React, { useState, useRef, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    TextInput,
    KeyboardAvoidingView,
    Platform,
    ActivityIndicator,
    Keyboard,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useQuery } from '@tanstack/react-query';

import { api } from '../api/client';
import { useAuth } from '../hooks/useAuth';

interface Message {
    id: string;
    text: string;
    sender: 'user' | 'agent';
    timestamp: Date;
    actions?: ActionButton[];
}

interface ActionButton {
    label: string;
    action: string;
    data?: any;
}

export function HomeScreen() {
    const navigation = useNavigation<any>();
    const { user } = useAuth();
    const scrollViewRef = useRef<ScrollView>(null);
    const messageIdCounter = useRef(1);

    const [messages, setMessages] = useState<Message[]>([
        {
            id: 'initial-1',
            text: `Hey ${user?.display_name || 'there'}! 💪 I'm your AI workout coach. What would you like to do today?`,
            sender: 'agent',
            timestamp: new Date(),
            actions: [
                { label: '🏋️ Generate Workout', action: 'generate_workout' },
                { label: '📸 Scan Equipment', action: 'scan_equipment' },
                { label: '💬 Chat About Fitness', action: 'chat' },
            ],
        },
    ]);
    const [inputText, setInputText] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    // Fetch user state for context
    const { data: stateData } = useQuery({
        queryKey: ['userState'],
        queryFn: async () => {
            const response = await api.state.get();
            return response.data;
        },
        staleTime: 1000 * 60 * 5,
    });

    useEffect(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
    }, [messages]);

    const [isKeyboardVisible, setKeyboardVisible] = useState(false);

    useEffect(() => {
        const keyboardShowListener = Keyboard.addListener(
            Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow',
            () => setKeyboardVisible(true)
        );
        const keyboardHideListener = Keyboard.addListener(
            Platform.OS === 'ios' ? 'keyboardWillHide' : 'keyboardDidHide',
            () => setKeyboardVisible(false)
        );

        return () => {
            keyboardShowListener.remove();
            keyboardHideListener.remove();
        };
    }, []);

    const handleActionPress = (action: string, data?: any) => {
        switch (action) {
            case 'generate_workout':
                addUserMessage("Generate a workout for me");
                handleGenerateWorkout();
                break;
            case 'scan_equipment':
                addUserMessage("I want to scan my equipment");
                navigation.navigate('ScanEquipment');
                break;
            case 'chat':
                addUserMessage("I want to chat about my fitness");
                addAgentMessage("Of course! Tell me about your fitness goals, how you're feeling today, or ask me any questions about workouts and nutrition. I'm here to help! 😊");
                break;
            case 'view_workout':
                if (data) {
                    navigation.navigate('WorkoutGen', { generatedPlan: data });
                }
                break;
            case 'start_workout':
                if (data?.plan_data?.exercises) {
                    navigation.navigate('ActiveSession', { exercises: data.plan_data.exercises });
                } else {
                    addAgentMessage("Sorry, I couldn't find the workout exercises. Please generate a new workout.");
                }
                break;
            default:
                break;
        }
    };

    const addUserMessage = (text: string) => {
        messageIdCounter.current += 1;
        const newMessage: Message = {
            id: `user-${messageIdCounter.current}-${Date.now()}`,
            text,
            sender: 'user',
            timestamp: new Date(),
        };
        setMessages(prev => [...prev, newMessage]);
    };

    const addAgentMessage = (text: string, actions?: ActionButton[]) => {
        messageIdCounter.current += 1;
        const newMessage: Message = {
            id: `agent-${messageIdCounter.current}-${Date.now()}`,
            text,
            sender: 'agent',
            timestamp: new Date(),
            actions,
        };
        setMessages(prev => [...prev, newMessage]);
    };

    const handleGenerateWorkout = async () => {
        setIsLoading(true);
        try {
            // Call the workout generation API with correct schema
            const response = await api.workout.generate({
                equipment: ['Bodyweight', 'Dumbbells'],
                duration_minutes: 30,
                fitness_level: 'Intermediate',
                goals: 'General Fitness',
                target_muscle_group: 'Full Body',
            });


            const workoutPlan = response.data;
            const exercises = workoutPlan.plan_data?.exercises || [];

            addAgentMessage(
                `I've created a ${workoutPlan.plan_data?.overview || 'personalized'} workout for you! It includes ${exercises.length} exercises. Ready to start?`,
                [
                    { label: '▶️ Start Workout', action: 'start_workout', data: workoutPlan },
                    { label: '👀 View Details', action: 'view_workout', data: workoutPlan },
                    { label: '🔄 Generate New', action: 'generate_workout' },
                ]
            );
        } catch (error: any) {
            console.error('Workout generation error:', error);
            addAgentMessage(
                `Sorry, I couldn't generate a workout right now. ${error.response?.data?.detail || error.message || 'Please try again!'}`
            );
        } finally {
            setIsLoading(false);
        }
    };

    const handleSendMessage = async () => {
        if (!inputText.trim() || isLoading) return;

        const userMessage = inputText.trim();
        addUserMessage(userMessage);
        setInputText('');
        setIsLoading(true);

        try {
            const response = await api.agent.chat(userMessage, {
                current_condition: stateData?.physical,
            });

            const agentResponse = response.data.response;
            let actions: ActionButton[] | undefined;

            if (response.data.action === 'view_workout') {
                actions = [{
                    label: '🏋️ View Workout Plan',
                    action: 'view_workout',
                    data: response.data.data
                }];
            } else if (userMessage.toLowerCase().includes('workout') || agentResponse.toLowerCase().includes('workout')) {
                // Fallback suggestion
                actions = [
                    { label: '🏋️ Generate Workout', action: 'generate_workout' },
                ];
            }

            addAgentMessage(agentResponse, actions);
        } catch (error) {
            addAgentMessage("Sorry, I'm having trouble connecting right now. Please try again!");
        } finally {
            setIsLoading(false);
        }
    };

    const renderMessage = (message: Message) => {
        const isUser = message.sender === 'user';

        return (
            <View
                key={message.id}
                style={[
                    styles.messageContainer,
                    isUser ? styles.userMessageContainer : styles.agentMessageContainer
                ]}
            >
                <View style={[
                    styles.messageBubble,
                    isUser ? styles.userBubble : styles.agentBubble
                ]}>
                    <Text style={[
                        styles.messageText,
                        isUser ? styles.userText : styles.agentText
                    ]}>
                        {message.text}
                    </Text>
                </View>

                {message.actions && (
                    <View style={styles.actionsContainer}>
                        {message.actions.map((action, index) => (
                            <TouchableOpacity
                                key={index}
                                style={styles.actionButton}
                                onPress={() => handleActionPress(action.action, action.data)}
                            >
                                <Text style={styles.actionButtonText}>{action.label}</Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                )}
            </View>
        );
    };

    return (
        <KeyboardAvoidingView
            style={styles.container}
            behavior={Platform.OS === 'ios' ? 'padding' : (isKeyboardVisible ? 'padding' : undefined)}
            keyboardVerticalOffset={0}
        >
            {/* Header */}
            <View style={styles.header}>
                <View>
                    <Text style={styles.greeting}>AI Coach</Text>
                    <Text style={styles.subtitle}>Your personal fitness assistant</Text>
                </View>
                <View style={styles.headerRight}>
                    <TouchableOpacity
                        style={styles.iconBtn}
                        onPress={() => navigation.navigate('VoiceCoach')}
                    >
                        <Text style={styles.iconText}>🎤</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                        style={styles.iconBtn}
                        onPress={() => navigation.navigate('ScanEquipment')}
                    >
                        <Text style={styles.iconText}>📸</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                        style={styles.iconBtn}
                        onPress={() => navigation.navigate('Profile')}
                    >
                        <Text style={styles.iconText}>👤</Text>
                    </TouchableOpacity>
                </View>
            </View>

            {/* Quick Stats Bar */}
            <View style={styles.statsBar}>
                <View style={styles.statItem}>
                    <Text style={styles.statValue}>
                        {typeof stateData?.physical?.workouts_this_week === 'number'
                            ? stateData.physical.workouts_this_week
                            : 0}
                    </Text>
                    <Text style={styles.statLabel}>Workouts</Text>
                </View>
                <View style={styles.statDivider} />
                <View style={styles.statItem}>
                    <Text style={styles.statValue}>
                        {typeof stateData?.physical?.active_minutes === 'number'
                            ? stateData.physical.active_minutes
                            : 0}
                    </Text>
                    <Text style={styles.statLabel}>Active Min</Text>
                </View>
                <View style={styles.statDivider} />
                <View style={styles.statItem}>
                    <Text style={[
                        styles.statValue,
                        { color: stateData?.physical?.recovery_status === 'well_rested' ? '#10B981' : '#F59E0B' }
                    ]}>
                        {String(stateData?.physical?.recovery_status || 'Ready').replace(/_/g, ' ')}
                    </Text>
                    <Text style={styles.statLabel}>Status</Text>
                </View>
            </View>

            {/* Chat Messages */}
            <ScrollView
                ref={scrollViewRef}
                style={styles.chatContainer}
                contentContainerStyle={styles.chatContent}
            >
                {messages.map(renderMessage)}

                {isLoading && (
                    <View style={styles.loadingContainer}>
                        <ActivityIndicator color="#6366F1" size="small" />
                        <Text style={styles.loadingText}>Thinking...</Text>
                    </View>
                )}
            </ScrollView>

            {/* Input Area */}
            <View style={styles.inputContainer}>
                <TextInput
                    style={styles.textInput}
                    placeholder="Ask me anything about fitness..."
                    placeholderTextColor="#6B7280"
                    value={inputText}
                    onChangeText={setInputText}
                    onSubmitEditing={handleSendMessage}
                    returnKeyType="send"
                    multiline
                />
                <TouchableOpacity
                    style={[styles.sendButton, !inputText.trim() && styles.sendButtonDisabled]}
                    onPress={handleSendMessage}
                    disabled={!inputText.trim() || isLoading}
                >
                    <Text style={styles.sendButtonText}>→</Text>
                </TouchableOpacity>
            </View>
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
        paddingHorizontal: 20,
        paddingTop: 60,
        paddingBottom: 16,
    },
    greeting: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#FFFFFF',
    },
    subtitle: {
        fontSize: 14,
        color: '#9CA3AF',
        marginTop: 2,
    },
    headerRight: {
        flexDirection: 'row',
        gap: 12,
    },
    iconBtn: {
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: '#1F1F1F',
        justifyContent: 'center',
        alignItems: 'center',
        borderWidth: 1,
        borderColor: '#333',
    },
    iconText: {
        fontSize: 20,
    },
    statsBar: {
        flexDirection: 'row',
        marginHorizontal: 20,
        backgroundColor: '#1F1F1F',
        borderRadius: 16,
        padding: 16,
        marginBottom: 16,
    },
    statItem: {
        flex: 1,
        alignItems: 'center',
    },
    statValue: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#FFFFFF',
        textTransform: 'capitalize',
    },
    statLabel: {
        fontSize: 11,
        color: '#9CA3AF',
        marginTop: 2,
    },
    statDivider: {
        width: 1,
        backgroundColor: '#333',
    },
    chatContainer: {
        flex: 1,
    },
    chatContent: {
        paddingHorizontal: 20,
        paddingBottom: 20,
    },
    messageContainer: {
        marginBottom: 16,
    },
    userMessageContainer: {
        alignItems: 'flex-end',
    },
    agentMessageContainer: {
        alignItems: 'flex-start',
    },
    messageBubble: {
        maxWidth: '85%',
        padding: 14,
        borderRadius: 20,
    },
    userBubble: {
        backgroundColor: '#6366F1',
        borderBottomRightRadius: 4,
    },
    agentBubble: {
        backgroundColor: '#1F1F1F',
        borderBottomLeftRadius: 4,
    },
    messageText: {
        fontSize: 15,
        lineHeight: 22,
    },
    userText: {
        color: '#FFFFFF',
    },
    agentText: {
        color: '#E5E7EB',
    },
    actionsContainer: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 8,
        marginTop: 10,
    },
    actionButton: {
        backgroundColor: '#2D2D3A',
        paddingVertical: 10,
        paddingHorizontal: 16,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: '#6366F1',
    },
    actionButtonText: {
        color: '#FFFFFF',
        fontSize: 14,
        fontWeight: '500',
    },
    loadingContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        paddingVertical: 10,
    },
    loadingText: {
        color: '#9CA3AF',
        fontSize: 14,
    },
    inputContainer: {
        flexDirection: 'row',
        alignItems: 'flex-end',
        paddingHorizontal: 20,
        paddingVertical: 16,
        backgroundColor: '#0A0A0A',
        borderTopWidth: 1,
        borderTopColor: '#1F1F1F',
    },
    textInput: {
        flex: 1,
        backgroundColor: '#1F1F1F',
        borderRadius: 24,
        paddingHorizontal: 20,
        paddingVertical: 12,
        paddingRight: 48,
        color: '#FFFFFF',
        fontSize: 15,
        maxHeight: 100,
        borderWidth: 1,
        borderColor: '#333',
    },
    sendButton: {
        position: 'absolute',
        right: 28,
        bottom: 24,
        width: 36,
        height: 36,
        borderRadius: 18,
        backgroundColor: '#6366F1',
        justifyContent: 'center',
        alignItems: 'center',
    },
    sendButtonDisabled: {
        backgroundColor: '#4B5563',
    },
    sendButtonText: {
        color: '#FFFFFF',
        fontSize: 18,
        fontWeight: 'bold',
    },
});
