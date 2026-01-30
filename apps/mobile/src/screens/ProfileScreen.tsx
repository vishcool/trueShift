import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, FlatList } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
// import { Ionicons } from '@expo/vector-icons';

export default function ProfileScreen() {
    const navigation = useNavigation<any>();
    const route = useRoute<any>();

    // In a real app, this would be in a global store (Zustand/Redux)
    // For now, we simulate "Todays Plan" with local state + route params
    const [todaysPlan, setTodaysPlan] = useState<any[]>([]);

    useEffect(() => {
        if (route.params?.addedExercises) {
            // Append new exercises to the plan
            setTodaysPlan(prev => [...prev, ...route.params.addedExercises]);
        }
    }, [route.params?.addedExercises]);

    const startSession = () => {
        if (todaysPlan.length === 0) return;
        navigation.navigate('ActiveSession', { exercises: todaysPlan });
    };

    const scanNew = () => {
        navigation.navigate('ScanEquipment');
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.headerTitle}>My Profile</Text>
                <Text style={styles.subTitle}>Ready to train</Text>
            </View>

            <ScrollView style={styles.content}>
                {/* Stats / Recovery Summary could go here */}

                <View style={styles.sectionHeader}>
                    <Text style={styles.sectionTitle}>Today's Session</Text>
                    <TouchableOpacity onPress={() => setTodaysPlan([])}>
                        {/* Clear button for demo */}
                        <Text style={styles.clearText}>Clear</Text>
                    </TouchableOpacity>
                </View>

                {todaysPlan.length === 0 ? (
                    <View style={styles.emptyState}>
                        <Text style={styles.emptyText}>No exercises added yet.</Text>
                        <Text style={styles.emptySubText}>Scan equipment to build your workout.</Text>
                    </View>
                ) : (
                    <View style={styles.planList}>
                        {todaysPlan.map((ex, idx) => (
                            <View key={idx} style={styles.planItem}>
                                <Text style={styles.planItemName}>{ex.name}</Text>
                                <Text style={styles.planItemMeta}>{ex.sets} x {ex.reps}</Text>
                            </View>
                        ))}
                    </View>
                )}

                <TouchableOpacity style={styles.scanButton} onPress={scanNew}>
                    <Text style={styles.scanButtonText}>+ Scan Equipment</Text>
                </TouchableOpacity>
            </ScrollView>

            {todaysPlan.length > 0 && (
                <View style={styles.footer}>
                    <TouchableOpacity style={styles.startButton} onPress={startSession}>
                        <Text style={styles.startButtonText}>Start Workout ({todaysPlan.length})</Text>
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
        paddingHorizontal: 24,
        paddingBottom: 20,
    },
    headerTitle: {
        color: 'white',
        fontSize: 28,
        fontWeight: 'bold',
    },
    subTitle: {
        color: '#6366F1',
        fontSize: 16,
        fontWeight: '600',
        marginTop: 4,
    },
    content: {
        flex: 1,
        paddingHorizontal: 24,
    },
    sectionHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: 20,
        marginBottom: 16,
    },
    sectionTitle: {
        color: 'white',
        fontSize: 18,
        fontWeight: 'bold',
    },
    clearText: {
        color: '#EF4444',
        fontSize: 14,
    },
    emptyState: {
        padding: 30,
        backgroundColor: '#1F1F1F',
        borderRadius: 16,
        alignItems: 'center',
        borderStyle: 'dashed',
        borderWidth: 2,
        borderColor: '#333',
        marginBottom: 20,
    },
    emptyText: {
        color: 'white',
        fontSize: 16,
        fontWeight: '600',
        marginBottom: 8,
    },
    emptySubText: {
        color: '#999',
        textAlign: 'center',
    },
    planList: {
        marginBottom: 20,
    },
    planItem: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        paddingVertical: 16,
        borderBottomWidth: 1,
        borderBottomColor: '#222',
    },
    planItemName: {
        color: 'white',
        fontSize: 16,
    },
    planItemMeta: {
        color: '#999',
    },
    scanButton: {
        backgroundColor: '#374151',
        paddingVertical: 16,
        borderRadius: 12,
        alignItems: 'center',
        marginBottom: 100, // Space for footer
    },
    scanButtonText: {
        color: 'white',
        fontWeight: 'bold',
        fontSize: 16,
    },
    footer: {
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        padding: 24,
        backgroundColor: 'rgba(10,10,10,0.95)',
        borderTopWidth: 1,
        borderTopColor: '#333',
    },
    startButton: {
        backgroundColor: '#6366F1',
        paddingVertical: 18,
        borderRadius: 12,
        alignItems: 'center',
    },
    startButtonText: {
        color: 'white',
        fontWeight: 'bold',
        fontSize: 16,
    },
});
