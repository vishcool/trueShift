import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
    ActivityIndicator,
    FlatList,
    KeyboardAvoidingView,
    Platform,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useQuery } from '@tanstack/react-query';

import { api, AgentChatResponse, DietPlanResponse } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import { ActionChip } from '../components/ui/ActionChip';
import { MessageBubble } from '../components/ui/MessageBubble';
import { SurfaceCard } from '../components/ui/SurfaceCard';

type CoachMode = 'general' | 'workout' | 'diet' | 'recovery';

type ActionType =
    | 'generate_workout'
    | 'view_workout'
    | 'start_workout'
    | 'voice'
    | 'scan_equipment'
    | 'generate_diet'
    | 'start_diet';

interface ActionButton {
    id: string;
    label: string;
    action: ActionType;
    data?: unknown;
}

interface Message {
    id: string;
    text: string;
    sender: 'user' | 'agent';
    actions?: ActionButton[];
}

interface WorkoutHistoryItem {
    id: string;
    created_at: string;
    status: string;
    plan_data: {
        overview?: string;
        exercises?: Array<{ name?: string; sets?: number | string; reps?: number | string }>;
    };
    completion_data?: {
        exercises?: Array<{
            performed_sets?: Array<{ weight?: string; reps?: string }>;
        }>;
    };
    feedback_notes?: string | null;
}

const MODE_LABELS: { id: CoachMode; label: string }[] = [
    { id: 'general', label: 'Coach' },
    { id: 'workout', label: 'Workout' },
    { id: 'diet', label: 'Diet' },
    { id: 'recovery', label: 'Recovery' },
];

const MODE_PROMPTS: Record<CoachMode, string[]> = {
    general: [
        'Plan my gym session for today',
        'How should I balance workout and diet this week?',
        'Give me a quick motivation check-in',
    ],
    workout: [
        'Build me a 40 min push workout',
        'I only have dumbbells, plan for legs',
        'Progressive overload plan for chest and triceps',
    ],
    diet: [
        'Create a high-protein vegetarian day plan',
        'Pre-workout and post-workout meal ideas',
        'I want fat loss diet guidance for weekdays',
    ],
    recovery: [
        'I am sore after leg day, what should I do?',
        'Give me a sleep and hydration recovery checklist',
        'Low-energy day: train or recover?',
    ],
};

const WORKOUT_DEFAULTS = {
    equipment: ['Bodyweight', 'Dumbbells'],
    duration_minutes: 35,
    fitness_level: 'Intermediate',
    goals: 'General Fitness',
    target_muscle_group: 'Full Body',
};

function createMessage(sender: 'user' | 'agent', text: string, actions?: ActionButton[]): Message {
    return {
        id: `${sender}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        sender,
        text,
        actions,
    };
}

function formatDietPlan(plan: DietPlanResponse): string {
    const macros = plan.macro_targets;
    const meals = plan.meal_templates.slice(0, 3).map((m) => `${m.timing}: ${m.options[0] || m.meal_name}`).join('\n');
    return [
        `Diet plan ready for goal: ${plan.goal}`,
        `Macros: ${macros.calories} kcal | P ${macros.protein_g}g | C ${macros.carbs_g}g | F ${macros.fats_g}g`,
        `Hydration: ${plan.hydration_target_liters}L/day`,
        meals ? `Sample meals:\n${meals}` : '',
    ].filter(Boolean).join('\n\n');
}

function formatWorkoutFromAction(data: any): string {
    const planData = data?.plan_data || data;
    const overview = planData?.overview || 'Workout generated.';
    const exercises = Array.isArray(planData?.exercises) ? planData.exercises : [];
    const list = exercises
        .slice(0, 5)
        .map((ex: any, idx: number) => `${idx + 1}. ${ex.name} - ${ex.sets} x ${ex.reps}`)
        .join('\n');

    return [overview, list].filter(Boolean).join('\n\n');
}

function formatWorkoutDate(isoDate: string): string {
    try {
        return new Date(isoDate).toLocaleDateString();
    } catch {
        return isoDate;
    }
}

function getCompletedSetCount(workout: WorkoutHistoryItem): number {
    const exercises = workout.completion_data?.exercises || [];
    return exercises.reduce((acc, ex) => acc + (ex.performed_sets?.length || 0), 0);
}

export function HomeScreen() {
    const navigation = useNavigation<any>();
    const { user } = useAuth();
    const listRef = useRef<FlatList<Message>>(null);

    const [mode, setMode] = useState<CoachMode>('general');
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);

    const { data: stateData } = useQuery({
        queryKey: ['userState'],
        queryFn: async () => {
            const response = await api.state.get();
            return response.data;
        },
        staleTime: 1000 * 60 * 5,
    });

    const { data: workoutHistory = [], isLoading: isWorkoutHistoryLoading } = useQuery({
        queryKey: ['workoutHistory'],
        queryFn: async () => {
            const response = await api.workout.getHistory();
            return response.data as WorkoutHistoryItem[];
        },
        staleTime: 1000 * 60 * 2,
    });

    useEffect(() => {
        const greeting = createMessage(
            'agent',
            `Welcome ${user?.display_name || 'there'}. I can coach via chat + voice, build workouts, and generate diet + recovery guidance.`,
            [
                { id: 'g-1', label: 'Start Voice Coach', action: 'voice' },
                { id: 'g-2', label: 'Generate Workout', action: 'generate_workout' },
                { id: 'g-3', label: 'Generate Diet Plan', action: 'generate_diet' },
            ]
        );
        setMessages([greeting]);
    }, [user?.display_name]);

    useEffect(() => {
        listRef.current?.scrollToEnd({ animated: true });
    }, [messages, isLoading]);

    const quickPrompts = useMemo(() => MODE_PROMPTS[mode], [mode]);

    const appendMessage = useCallback((msg: Message) => {
        setMessages(prev => [...prev, msg]);
    }, []);

    const handleGenerateWorkout = useCallback(async () => {
        setIsLoading(true);
        try {
            const response = await api.workout.generate(WORKOUT_DEFAULTS);
            const workoutPlan = response.data;
            const exercises = workoutPlan.plan_data?.exercises || [];

            appendMessage(createMessage(
                'agent',
                `Workout ready. ${workoutPlan.plan_data?.overview || 'Custom plan'} with ${exercises.length} exercises.`,
                [
                    { id: 'w-1', label: 'Start Workout', action: 'start_workout', data: workoutPlan },
                    { id: 'w-2', label: 'View Plan', action: 'view_workout', data: workoutPlan },
                ]
            ));
        } catch (error: any) {
            appendMessage(createMessage('agent', `Could not generate workout. ${error?.response?.data?.detail || 'Retry shortly.'}`));
        } finally {
            setIsLoading(false);
        }
    }, [appendMessage]);

    const handleGenerateDiet = useCallback(async () => {
        setIsLoading(true);
        try {
            const response = await api.diet.generate({
                goal: 'Gym performance and fat loss',
                meals_per_day: 4,
                dietary_preferences: ['High Protein'],
            });
            appendMessage(createMessage('agent', formatDietPlan(response.data), [
                { id: 'd-1', label: 'Start Diet Plan', action: 'start_diet', data: response.data }
            ]));
        } catch (error: any) {
            appendMessage(createMessage('agent', `Could not generate diet plan. ${error?.response?.data?.detail || 'Retry shortly.'}`));
        } finally {
            setIsLoading(false);
        }
    }, [appendMessage]);

    const handleAction = useCallback((action: ActionType, data?: unknown) => {
        if (action === 'generate_workout') {
            appendMessage(createMessage('user', 'Generate a workout plan for me.'));
            handleGenerateWorkout();
            return;
        }

        if (action === 'generate_diet') {
            appendMessage(createMessage('user', 'Generate a practical diet plan for me.'));
            handleGenerateDiet();
            return;
        }

        if (action === 'scan_equipment') {
            navigation.navigate('ScanEquipment');
            return;
        }

        if (action === 'voice') {
            navigation.navigate('VoiceCoach', { initialMode: mode });
            return;
        }

        if (action === 'view_workout') {
            navigation.navigate('WorkoutGen', { generatedPlan: data });
            return;
        }

        if (action === 'start_diet') {
            navigation.navigate('DietPlan', { plan: data });
            return;
        }

        if (action === 'start_workout') {
            const plan = data as { plan_data?: { exercises?: unknown[] }; exercises?: unknown[] } | undefined;
            const exercises = plan?.plan_data?.exercises || plan?.exercises;

            if (Array.isArray(exercises) && exercises.length > 0) {
                navigation.navigate('ActiveSession', { exercises });
            } else {
                appendMessage(createMessage('agent', 'No exercises found. Please generate again.'));
            }
        }
    }, [appendMessage, handleGenerateDiet, handleGenerateWorkout, mode, navigation]);

    const submitMessage = useCallback(async (textValue?: string) => {
        if (isLoading) {
            return;
        }

        const text = (textValue ?? input).trim();
        if (!text) {
            return;
        }

        appendMessage(createMessage('user', text));
        setInput('');
        setIsLoading(true);

        try {
            const response = await api.agent.chat(text, {
                coach_mode: mode,
                current_condition: stateData?.physical,
                goals: stateData?.goals,
            });

            const payload: AgentChatResponse = response.data;
            const actions: ActionButton[] = [];

            if (payload.action === 'view_workout') {
                actions.push({
                    id: 'a-1',
                    label: 'Open Workout Plan',
                    action: 'view_workout',
                    data: payload.data,
                });
                actions.push({
                    id: 'a-1b',
                    label: 'Start Workout',
                    action: 'start_workout',
                    data: payload.data,
                });
            }

            if (mode === 'workout') {
                actions.push({ id: 'a-2', label: 'Generate Workout', action: 'generate_workout' });
            }
            if (mode === 'diet') {
                actions.push({ id: 'a-3', label: 'Generate Diet', action: 'generate_diet' });
            }

            appendMessage(createMessage('agent', payload.response || 'I could not produce a response.', actions.length ? actions : undefined));
            if (payload.action === 'view_workout' && payload.data) {
                appendMessage(createMessage('agent', formatWorkoutFromAction(payload.data)));
            }
        } catch {
            appendMessage(createMessage('agent', 'Connection issue. Please try again in a moment.'));
        } finally {
            setIsLoading(false);
        }
    }, [appendMessage, input, isLoading, mode, stateData?.goals, stateData?.physical]);

    const startConversationFromWorkout = useCallback(async (workout: WorkoutHistoryItem) => {
        const workoutPrompt = `Let's continue from my past workout (${formatWorkoutDate(workout.created_at)}): ${workout.plan_data?.overview || 'workout session'}. Give me next-step coaching and progression.`;
        appendMessage(createMessage('user', workoutPrompt));
        setIsLoading(true);
        setMode('workout');

        try {
            const response = await api.agent.chat(workoutPrompt, {
                coach_mode: 'workout',
                current_plan: workout,
                source_workout_id: workout.id,
                source_workout_status: workout.status,
            });

            const payload: AgentChatResponse = response.data;
            const actions: ActionButton[] = [];

            if (payload.action === 'view_workout') {
                actions.push({
                    id: `history-view-${workout.id}`,
                    label: 'Open Workout Plan',
                    action: 'view_workout',
                    data: payload.data,
                });
                actions.push({
                    id: `history-start-${workout.id}`,
                    label: 'Start Workout',
                    action: 'start_workout',
                    data: payload.data,
                });
            }

            appendMessage(createMessage('agent', payload.response || 'I could not produce a response.', actions.length ? actions : undefined));
            if (payload.action === 'view_workout' && payload.data) {
                appendMessage(createMessage('agent', formatWorkoutFromAction(payload.data)));
            }
        } catch {
            appendMessage(createMessage('agent', 'Unable to load coaching from that workout right now.'));
        } finally {
            setIsLoading(false);
        }
    }, [appendMessage]);

    const renderMessage = ({ item }: { item: Message }) => {
        const actionFooter = item.actions?.length ? (
            <View style={styles.actionRow}>
                {item.actions.map((action) => (
                    <ActionChip
                        key={action.id}
                        label={action.label}
                        onPress={() => handleAction(action.action, action.data)}
                    />
                ))}
            </View>
        ) : undefined;

        return (
            <MessageBubble
                role={item.sender}
                text={item.text}
                footer={actionFooter}
            />
        );
    };

    return (
        <KeyboardAvoidingView
            style={styles.container}
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            keyboardVerticalOffset={0}
        >
            <View style={styles.header}>
                <View>
                    <Text style={styles.title}>TrueShift Coach</Text>
                    <Text style={styles.subtitle}>Multimodal gym assistant</Text>
                </View>
                <TouchableOpacity style={styles.profileBtn} onPress={() => navigation.navigate('Profile')}>
                    <Text style={styles.profileText}>Profile</Text>
                </TouchableOpacity>
            </View>

            <View style={styles.modeRow}>
                {MODE_LABELS.map((item) => (
                    <ActionChip
                        key={item.id}
                        label={item.label}
                        active={mode === item.id}
                        onPress={() => setMode(item.id)}
                        style={styles.modeChip}
                    />
                ))}
            </View>

            <SurfaceCard style={styles.metricsCard}>
                <View style={styles.metricItem}>
                    <Text style={styles.metricValue}>{typeof stateData?.physical?.workouts_this_week === 'number' ? stateData.physical.workouts_this_week : 0}</Text>
                    <Text style={styles.metricLabel}>Workouts</Text>
                </View>
                <View style={styles.metricDivider} />
                <View style={styles.metricItem}>
                    <Text style={styles.metricValue}>{typeof stateData?.physical?.active_minutes === 'number' ? stateData.physical.active_minutes : 0}</Text>
                    <Text style={styles.metricLabel}>Active Min</Text>
                </View>
                <View style={styles.metricDivider} />
                <View style={styles.metricItem}>
                    <Text style={styles.metricValueSmall}>{String(stateData?.physical?.recovery_status || 'ready').replace(/_/g, ' ')}</Text>
                    <Text style={styles.metricLabel}>Recovery</Text>
                </View>
            </SurfaceCard>

            <View style={styles.historySection}>
                <View style={styles.historyHeader}>
                    <Text style={styles.historyTitle}>Past Workouts</Text>
                    <Text style={styles.historySubtitle}>Resume coaching from your history</Text>
                </View>

                {isWorkoutHistoryLoading ? (
                    <View style={styles.historyLoading}>
                        <ActivityIndicator size="small" color="#2563EB" />
                        <Text style={styles.historyLoadingText}>Loading workouts...</Text>
                    </View>
                ) : workoutHistory.length === 0 ? (
                    <SurfaceCard style={styles.historyEmptyCard}>
                        <Text style={styles.historyEmptyText}>No workouts logged yet. Complete one session to build your dashboard.</Text>
                    </SurfaceCard>
                ) : (
                    <ScrollView
                        horizontal
                        showsHorizontalScrollIndicator={false}
                        contentContainerStyle={styles.historyScrollContent}
                    >
                        {workoutHistory.slice(0, 8).map((workout) => {
                            const exerciseCount = workout.plan_data?.exercises?.length || 0;
                            const completedSets = getCompletedSetCount(workout);
                            return (
                                <SurfaceCard key={workout.id} style={styles.historyCard}>
                                    <Text style={styles.historyCardDate}>{formatWorkoutDate(workout.created_at)}</Text>
                                    <Text style={styles.historyCardOverview} numberOfLines={2}>
                                        {workout.plan_data?.overview || 'Workout Session'}
                                    </Text>
                                    <Text style={styles.historyCardMeta}>
                                        {exerciseCount} exercises • {completedSets} sets logged
                                    </Text>
                                    <Text style={styles.historyCardStatus}>
                                        Status: {workout.status.replace('_', ' ')}
                                    </Text>
                                    <View style={styles.historyActionRow}>
                                        <ActionChip
                                            label="View"
                                            onPress={() => navigation.navigate('WorkoutGen', { generatedPlan: workout })}
                                        />
                                        <ActionChip
                                            label="Ask Coach"
                                            onPress={() => startConversationFromWorkout(workout)}
                                        />
                                    </View>
                                </SurfaceCard>
                            );
                        })}
                    </ScrollView>
                )}
            </View>

            <View style={styles.quickPromptWrap}>
                {quickPrompts.map((prompt) => (
                    <ActionChip key={prompt} label={prompt} onPress={() => submitMessage(prompt)} />
                ))}
            </View>

            <FlatList
                ref={listRef}
                data={messages}
                keyExtractor={(item) => item.id}
                renderItem={renderMessage}
                contentContainerStyle={styles.listContent}
                style={styles.list}
            />

            {isLoading && (
                <View style={styles.loadingRow}>
                    <ActivityIndicator size="small" color="#2563EB" />
                    <Text style={styles.loadingText}>Coach is thinking...</Text>
                </View>
            )}

            <View style={styles.inputWrap}>
                <TouchableOpacity style={styles.voiceBtn} onPress={() => navigation.navigate('VoiceCoach', { initialMode: mode })}>
                    <Text style={styles.voiceBtnText}>Voice</Text>
                </TouchableOpacity>
                <TextInput
                    style={styles.input}
                    value={input}
                    onChangeText={setInput}
                    placeholder={`Ask your ${mode} coach...`}
                    placeholderTextColor="#6B7280"
                    onSubmitEditing={() => submitMessage()}
                    returnKeyType="send"
                    multiline
                />
                <TouchableOpacity
                    style={[styles.sendBtn, (!input.trim() || isLoading) && styles.sendBtnDisabled]}
                    onPress={() => submitMessage()}
                    disabled={!input.trim() || isLoading}
                >
                    <Text style={styles.sendBtnText}>Send</Text>
                </TouchableOpacity>
            </View>
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
        paddingHorizontal: 18,
        paddingBottom: 10,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    title: {
        color: '#F5F5F5',
        fontSize: 24,
        fontWeight: '700',
    },
    subtitle: {
        color: '#9CA3AF',
        fontSize: 13,
        marginTop: 2,
    },
    profileBtn: {
        backgroundColor: '#131313',
        borderWidth: 1,
        borderColor: '#2F2F2F',
        paddingHorizontal: 14,
        paddingVertical: 8,
        borderRadius: 16,
    },
    profileText: {
        color: '#E5E7EB',
        fontSize: 12,
        fontWeight: '600',
    },
    modeRow: {
        flexDirection: 'row',
        paddingHorizontal: 14,
        marginTop: 4,
        gap: 8,
    },
    modeChip: {
        flex: 1,
        alignItems: 'center',
    },
    metricsCard: {
        flexDirection: 'row',
        marginHorizontal: 18,
        marginTop: 14,
        paddingVertical: 14,
    },
    metricItem: {
        flex: 1,
        alignItems: 'center',
    },
    metricValue: {
        color: '#F5F5F5',
        fontSize: 18,
        fontWeight: '700',
    },
    metricValueSmall: {
        color: '#D1D5DB',
        fontSize: 14,
        fontWeight: '700',
        textTransform: 'capitalize',
    },
    metricLabel: {
        color: '#9CA3AF',
        fontSize: 11,
        marginTop: 2,
    },
    metricDivider: {
        width: 1,
        backgroundColor: '#2F2F2F',
    },
    historySection: {
        marginTop: 12,
        paddingHorizontal: 16,
    },
    historyHeader: {
        marginBottom: 8,
    },
    historyTitle: {
        color: '#F3F4F6',
        fontSize: 16,
        fontWeight: '700',
    },
    historySubtitle: {
        color: '#9CA3AF',
        fontSize: 12,
        marginTop: 2,
    },
    historyLoading: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        paddingVertical: 8,
    },
    historyLoadingText: {
        color: '#9CA3AF',
        fontSize: 12,
    },
    historyEmptyCard: {
        padding: 12,
    },
    historyEmptyText: {
        color: '#9CA3AF',
        fontSize: 13,
        lineHeight: 20,
    },
    historyScrollContent: {
        gap: 10,
        paddingRight: 8,
    },
    historyCard: {
        width: 250,
        padding: 12,
    },
    historyCardDate: {
        color: '#9CA3AF',
        fontSize: 12,
        marginBottom: 4,
    },
    historyCardOverview: {
        color: '#F9FAFB',
        fontSize: 14,
        fontWeight: '700',
        marginBottom: 6,
        lineHeight: 20,
    },
    historyCardMeta: {
        color: '#D1D5DB',
        fontSize: 12,
        marginBottom: 4,
    },
    historyCardStatus: {
        color: '#93C5FD',
        fontSize: 12,
        marginBottom: 10,
        textTransform: 'capitalize',
    },
    historyActionRow: {
        flexDirection: 'row',
        gap: 8,
    },
    quickPromptWrap: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        paddingHorizontal: 16,
        marginTop: 12,
        gap: 8,
    },
    list: {
        flex: 1,
        marginTop: 8,
    },
    listContent: {
        paddingHorizontal: 16,
        paddingBottom: 10,
    },
    actionRow: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 8,
        marginTop: 8,
        maxWidth: '90%',
    },
    loadingRow: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 8,
        paddingHorizontal: 20,
        paddingBottom: 8,
    },
    loadingText: {
        color: '#9CA3AF',
        fontSize: 12,
    },
    inputWrap: {
        flexDirection: 'row',
        alignItems: 'flex-end',
        borderTopWidth: 1,
        borderTopColor: '#222222',
        paddingHorizontal: 12,
        paddingVertical: 12,
        backgroundColor: '#070707',
    },
    voiceBtn: {
        height: 42,
        paddingHorizontal: 12,
        borderRadius: 12,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#141414',
        borderWidth: 1,
        borderColor: '#2F2F2F',
        marginRight: 8,
    },
    voiceBtnText: {
        color: '#F3F4F6',
        fontSize: 12,
        fontWeight: '700',
    },
    input: {
        flex: 1,
        backgroundColor: '#131313',
        borderWidth: 1,
        borderColor: '#2F2F2F',
        borderRadius: 14,
        paddingHorizontal: 12,
        paddingVertical: 10,
        color: '#F3F4F6',
        maxHeight: 90,
        fontSize: 14,
        marginRight: 8,
    },
    sendBtn: {
        height: 42,
        paddingHorizontal: 14,
        borderRadius: 12,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#2563EB',
    },
    sendBtnDisabled: {
        opacity: 0.5,
    },
    sendBtnText: {
        color: '#F4FFFB',
        fontSize: 13,
        fontWeight: '700',
    },
});
