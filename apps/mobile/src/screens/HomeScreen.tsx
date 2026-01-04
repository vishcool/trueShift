/**
 * TrueShift - Home Screen
 * 
 * Main dashboard showing user state and recommendations.
 */

import React from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    RefreshControl,
    TouchableOpacity,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';

import { api } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import { offlineCache } from '../services/OfflineCache';

export function HomeScreen() {
    const { user, logout } = useAuth();

    // Fetch user state
    const {
        data: stateData,
        isLoading: stateLoading,
        refetch: refetchState,
    } = useQuery({
        queryKey: ['userState'],
        queryFn: async () => {
            const response = await api.state.get();
            await offlineCache.userState.set(response.data);
            return response.data;
        },
        staleTime: 1000 * 60 * 5,
    });

    // Fetch recommendations
    const {
        data: recsData,
        isLoading: recsLoading,
    } = useQuery({
        queryKey: ['recommendations'],
        queryFn: async () => {
            const response = await api.state.getRecommendations(3);
            await offlineCache.recommendations.set(response.data);
            return response.data;
        },
        staleTime: 1000 * 60 * 15,
    });

    const isLoading = stateLoading || recsLoading;

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <View>
                    <Text style={styles.greeting}>
                        Hey, {user?.display_name || 'Athlete'} 👋
                    </Text>
                    <Text style={styles.subtitle}>Ready to crush it today?</Text>
                </View>
                <TouchableOpacity onPress={logout} style={styles.logoutBtn}>
                    <Text style={styles.logoutText}>Logout</Text>
                </TouchableOpacity>
            </View>

            <ScrollView
                style={styles.content}
                refreshControl={
                    <RefreshControl
                        refreshing={isLoading}
                        onRefresh={() => refetchState()}
                        tintColor="#6366F1"
                    />
                }
            >
                {/* Status Cards */}
                <View style={styles.statusGrid}>
                    <View style={styles.statusCard}>
                        <Text style={styles.statusValue}>
                            {stateData?.physical?.steps_today || 0}
                        </Text>
                        <Text style={styles.statusLabel}>Steps</Text>
                    </View>
                    <View style={styles.statusCard}>
                        <Text style={styles.statusValue}>
                            {stateData?.physical?.active_minutes || 0}
                        </Text>
                        <Text style={styles.statusLabel}>Active Min</Text>
                    </View>
                    <View style={styles.statusCard}>
                        <Text style={styles.statusValue}>
                            {stateData?.physical?.workouts_this_week || 0}
                        </Text>
                        <Text style={styles.statusLabel}>Workouts</Text>
                    </View>
                </View>

                {/* Recovery Status */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Recovery Status</Text>
                    <View style={styles.recoveryCard}>
                        <Text style={styles.recoveryStatus}>
                            {stateData?.physical?.recovery_status?.replace('_', ' ') || 'Unknown'}
                        </Text>
                        <Text style={styles.recoverySubtext}>
                            Based on sleep and activity data
                        </Text>
                    </View>
                </View>

                {/* Recommendations */}
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>For You</Text>
                    {recsData?.recommendations?.map((rec: any, index: number) => (
                        <TouchableOpacity key={index} style={styles.recommendationCard}>
                            <Text style={styles.recTitle}>{rec.title}</Text>
                            <Text style={styles.recDescription}>{rec.description}</Text>
                            <View style={styles.recBadge}>
                                <Text style={styles.recBadgeText}>{rec.type}</Text>
                            </View>
                        </TouchableOpacity>
                    ))}
                    {(!recsData?.recommendations || recsData.recommendations.length === 0) && (
                        <Text style={styles.emptyText}>
                            No recommendations yet. Keep moving!
                        </Text>
                    )}
                </View>
            </ScrollView>
        </View>
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
        paddingBottom: 20,
    },
    greeting: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#FFFFFF',
    },
    subtitle: {
        fontSize: 16,
        color: '#9CA3AF',
        marginTop: 4,
    },
    logoutBtn: {
        padding: 10,
    },
    logoutText: {
        color: '#6366F1',
        fontSize: 14,
    },
    content: {
        flex: 1,
        paddingHorizontal: 20,
    },
    statusGrid: {
        flexDirection: 'row',
        gap: 12,
        marginBottom: 24,
    },
    statusCard: {
        flex: 1,
        backgroundColor: '#1F1F1F',
        borderRadius: 16,
        padding: 16,
        alignItems: 'center',
    },
    statusValue: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#FFFFFF',
    },
    statusLabel: {
        fontSize: 12,
        color: '#9CA3AF',
        marginTop: 4,
    },
    section: {
        marginBottom: 24,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: '600',
        color: '#FFFFFF',
        marginBottom: 12,
    },
    recoveryCard: {
        backgroundColor: '#1F1F1F',
        borderRadius: 16,
        padding: 20,
    },
    recoveryStatus: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#10B981',
        textTransform: 'capitalize',
    },
    recoverySubtext: {
        fontSize: 14,
        color: '#9CA3AF',
        marginTop: 4,
    },
    recommendationCard: {
        backgroundColor: '#1F1F1F',
        borderRadius: 16,
        padding: 20,
        marginBottom: 12,
    },
    recTitle: {
        fontSize: 18,
        fontWeight: '600',
        color: '#FFFFFF',
    },
    recDescription: {
        fontSize: 14,
        color: '#9CA3AF',
        marginTop: 8,
    },
    recBadge: {
        backgroundColor: '#6366F1',
        borderRadius: 8,
        paddingHorizontal: 10,
        paddingVertical: 4,
        alignSelf: 'flex-start',
        marginTop: 12,
    },
    recBadgeText: {
        fontSize: 12,
        color: '#FFFFFF',
        textTransform: 'uppercase',
    },
    emptyText: {
        fontSize: 14,
        color: '#6B7280',
        textAlign: 'center',
        paddingVertical: 20,
    },
});
