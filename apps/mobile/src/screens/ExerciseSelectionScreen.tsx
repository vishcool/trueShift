import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
// import { Ionicons } from '@expo/vector-icons'; // Assuming Icons are available

export default function ExerciseSelectionScreen() {
    const navigation = useNavigation<any>();
    const route = useRoute<any>();
    const { suggestions, analysis } = route.params || {};

    // State to track selected exercises
    const [selectedExercises, setSelectedExercises] = useState<any[]>([]);

    useEffect(() => {
        if (suggestions) {
            // Default select all? Or let user pick. Let's select all by default for ease.
            setSelectedExercises([...suggestions]);
        }
    }, [suggestions]);

    const toggleSelection = (exercise: any) => {
        if (selectedExercises.find(e => e.name === exercise.name)) {
            setSelectedExercises(selectedExercises.filter(e => e.name !== exercise.name));
        } else {
            setSelectedExercises([...selectedExercises, exercise]);
        }
    };

    const isSelected = (exercise: any) => {
        return !!selectedExercises.find(e => e.name === exercise.name);
    };

    const addToPlan = () => {
        if (selectedExercises.length === 0) {
            Alert.alert("Selection Required", "Please select at least one exercise to add.");
            return;
        }

        // Navigate to Profile or Active Session with these new exercises appended
        // Ideally we have a global store or we pass back to Profile
        navigation.navigate('Profile', {
            addedExercises: selectedExercises
        });
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backBtn}>
                    <Text style={styles.backText}>Cancel</Text>
                </TouchableOpacity>
                <Text style={styles.title}>Machine Detected</Text>
            </View>

            <ScrollView style={styles.content}>
                {analysis && (
                    <View style={styles.analysisBox}>
                        <Text style={styles.analysisTitle}>AI Coach Insight</Text>
                        <Text style={styles.analysisText}>{analysis}</Text>
                    </View>
                )}

                <Text style={styles.sectionTitle}>Suggested Exercises</Text>

                {suggestions && suggestions.map((ex: any, idx: number) => (
                    <TouchableOpacity
                        key={idx}
                        style={[styles.card, isSelected(ex) && styles.selectedCard]}
                        onPress={() => toggleSelection(ex)}
                    >
                        <View style={styles.cardHeader}>
                            <Text style={styles.exName}>{ex.name}</Text>
                            <View style={[styles.checkbox, isSelected(ex) && styles.checkedBox]} />
                        </View>
                        <Text style={styles.exMeta}>{ex.sets} sets × {ex.reps} • {ex.notes}</Text>
                    </TouchableOpacity>
                ))}
            </ScrollView>

            <View style={styles.footer}>
                <TouchableOpacity style={styles.addButton} onPress={addToPlan}>
                    <Text style={styles.addButtonText}>Add {selectedExercises.length} to Session</Text>
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
    header: {
        paddingTop: 60,
        paddingHorizontal: 20,
        paddingBottom: 20,
        flexDirection: 'row',
        alignItems: 'center',
        borderBottomWidth: 1,
        borderBottomColor: '#333',
    },
    backBtn: {
        marginRight: 20,
    },
    backText: {
        color: '#999',
        fontSize: 16,
    },
    title: {
        color: 'white',
        fontSize: 20,
        fontWeight: 'bold',
    },
    content: {
        padding: 20,
    },
    analysisBox: {
        backgroundColor: 'rgba(99, 102, 241, 0.15)',
        padding: 15,
        borderRadius: 10,
        marginBottom: 25,
        borderLeftWidth: 3,
        borderLeftColor: '#6366F1',
    },
    analysisTitle: {
        color: '#818CF8',
        fontWeight: 'bold',
        marginBottom: 5,
        fontSize: 14,
    },
    analysisText: {
        color: '#E0E7FF',
        fontSize: 14,
        lineHeight: 20,
    },
    sectionTitle: {
        color: 'white',
        fontSize: 18,
        fontWeight: 'bold',
        marginBottom: 15,
    },
    card: {
        backgroundColor: '#1F1F1F',
        borderRadius: 12,
        padding: 15,
        marginBottom: 12,
        borderWidth: 1,
        borderColor: '#333',
    },
    selectedCard: {
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
    },
    cardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 5,
    },
    exName: {
        color: 'white',
        fontSize: 16,
        fontWeight: '600',
    },
    exMeta: {
        color: '#999',
        fontSize: 14,
    },
    checkbox: {
        width: 20,
        height: 20,
        borderRadius: 10,
        borderWidth: 2,
        borderColor: '#666',
    },
    checkedBox: {
        backgroundColor: '#10B981',
        borderColor: '#10B981',
    },
    footer: {
        padding: 20,
        paddingBottom: 40,
        backgroundColor: '#0A0A0A',
        borderTopWidth: 1,
        borderTopColor: '#333',
    },
    addButton: {
        backgroundColor: '#10B981',
        padding: 16,
        borderRadius: 12,
        alignItems: 'center',
    },
    addButtonText: {
        color: 'white',
        fontWeight: 'bold',
        fontSize: 16,
    }
});
