import React, { useMemo, useState } from 'react';
import {
    Alert,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';

import { useAuth } from '../hooks/useAuth';
import { SurfaceCard } from '../components/ui/SurfaceCard';

export default function ProfileScreen() {
    const navigation = useNavigation<any>();
    const { user, logout, updateProfile } = useAuth();

    const existingProfile = useMemo(() => {
        const preferences = (user?.preferences as any) || {};
        return preferences.fitness_profile || {};
    }, [user?.preferences]);

    const [displayName, setDisplayName] = useState(user?.display_name || '');
    const [fitnessLevel, setFitnessLevel] = useState(existingProfile.level || 'Intermediate');
    const [goalsText, setGoalsText] = useState((existingProfile.goals || []).join(', '));
    const [equipmentText, setEquipmentText] = useState((existingProfile.equipment || []).join(', '));
    const [saving, setSaving] = useState(false);

    const parseCsv = (value: string) =>
        value
            .split(',')
            .map((item) => item.trim())
            .filter(Boolean);

    const handleSaveProfile = async () => {
        try {
            setSaving(true);
            await updateProfile({
                display_name: displayName.trim(),
                fitness_level: fitnessLevel.trim(),
                fitness_goals: parseCsv(goalsText),
                equipment: parseCsv(equipmentText),
            });
            Alert.alert('Saved', 'Profile updated successfully.');
        } catch {
            Alert.alert('Error', 'Failed to update profile.');
        } finally {
            setSaving(false);
        }
    };

    const handleGoBack = () => {
        if (navigation.canGoBack()) {
            navigation.goBack();
        } else {
            navigation.navigate('Home');
        }
    };

    const handleLogout = () => {
        Alert.alert('Logout', 'Are you sure you want to logout?', [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Logout', style: 'destructive', onPress: logout },
        ]);
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={handleGoBack}>
                    <Text style={styles.backButtonText}>Back</Text>
                </TouchableOpacity>
                <Text style={styles.headerTitle}>My Profile</Text>
                <View style={{ width: 44 }} />
            </View>

            <ScrollView style={styles.content} contentContainerStyle={styles.contentInner}>
                <View style={styles.avatarSection}>
                    <View style={styles.avatar}>
                        <Text style={styles.avatarText}>{displayName?.charAt(0).toUpperCase() || 'U'}</Text>
                    </View>
                    <Text style={styles.displayName}>{displayName || 'User'}</Text>
                    <Text style={styles.email}>{user?.email || 'No email'}</Text>
                </View>

                <Text style={styles.sectionTitle}>Edit Profile</Text>
                <SurfaceCard style={styles.card}>
                    <Text style={styles.label}>Display Name</Text>
                    <TextInput
                        style={styles.input}
                        value={displayName}
                        onChangeText={setDisplayName}
                        placeholder="Your name"
                        placeholderTextColor="#6B7280"
                    />

                    <Text style={styles.label}>Fitness Level</Text>
                    <TextInput
                        style={styles.input}
                        value={fitnessLevel}
                        onChangeText={setFitnessLevel}
                        placeholder="Beginner / Intermediate / Advanced"
                        placeholderTextColor="#6B7280"
                    />

                    <Text style={styles.label}>Goals (comma separated)</Text>
                    <TextInput
                        style={styles.input}
                        value={goalsText}
                        onChangeText={setGoalsText}
                        placeholder="Fat Loss, Strength, Endurance"
                        placeholderTextColor="#6B7280"
                    />

                    <Text style={styles.label}>Equipment (comma separated)</Text>
                    <TextInput
                        style={styles.input}
                        value={equipmentText}
                        onChangeText={setEquipmentText}
                        placeholder="Dumbbells, Barbell"
                        placeholderTextColor="#6B7280"
                    />

                    <TouchableOpacity style={styles.saveButton} onPress={handleSaveProfile} disabled={saving}>
                        <Text style={styles.saveButtonText}>{saving ? 'Saving...' : 'Save Profile'}</Text>
                    </TouchableOpacity>
                </SurfaceCard>

                <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
                    <Text style={styles.logoutButtonText}>Logout</Text>
                </TouchableOpacity>
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#050505',
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingTop: 58,
        paddingHorizontal: 16,
        paddingBottom: 14,
        borderBottomWidth: 1,
        borderBottomColor: '#222222',
    },
    backButtonText: {
        color: '#93C5FD',
        fontSize: 16,
    },
    headerTitle: {
        color: '#F9FAFB',
        fontSize: 20,
        fontWeight: '700',
    },
    content: {
        flex: 1,
    },
    contentInner: {
        padding: 16,
        paddingBottom: 28,
    },
    avatarSection: {
        alignItems: 'center',
        marginBottom: 20,
    },
    avatar: {
        width: 80,
        height: 80,
        borderRadius: 40,
        backgroundColor: '#1F2937',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 12,
    },
    avatarText: {
        color: '#FFFFFF',
        fontSize: 30,
        fontWeight: '700',
    },
    displayName: {
        color: '#F9FAFB',
        fontSize: 22,
        fontWeight: '700',
        marginBottom: 4,
    },
    email: {
        color: '#9CA3AF',
        fontSize: 14,
    },
    sectionTitle: {
        color: '#E5E7EB',
        fontSize: 17,
        fontWeight: '700',
        marginBottom: 10,
    },
    card: {
        padding: 14,
    },
    label: {
        color: '#D1D5DB',
        fontSize: 13,
        marginBottom: 6,
        marginTop: 4,
    },
    input: {
        backgroundColor: '#0F0F0F',
        borderWidth: 1,
        borderColor: '#2F2F2F',
        borderRadius: 10,
        paddingHorizontal: 12,
        paddingVertical: 10,
        color: '#F3F4F6',
        fontSize: 14,
        marginBottom: 6,
    },
    saveButton: {
        marginTop: 12,
        backgroundColor: '#2563EB',
        borderRadius: 10,
        alignItems: 'center',
        paddingVertical: 12,
    },
    saveButtonText: {
        color: '#FFFFFF',
        fontSize: 14,
        fontWeight: '700',
    },
    logoutButton: {
        marginTop: 16,
        borderWidth: 1,
        borderColor: '#B91C1C',
        borderRadius: 10,
        alignItems: 'center',
        paddingVertical: 12,
    },
    logoutButtonText: {
        color: '#F87171',
        fontSize: 14,
        fontWeight: '700',
    },
});
