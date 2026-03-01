import React from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';

import { DietPlanResponse } from '../api/client';
import { SurfaceCard } from '../components/ui/SurfaceCard';

export default function DietPlanScreen() {
    const navigation = useNavigation<any>();
    const route = useRoute<any>();
    const plan = route.params?.plan as DietPlanResponse | undefined;

    if (!plan) {
        return (
            <View style={styles.container}>
                <View style={styles.header}>
                    <TouchableOpacity onPress={() => navigation.goBack()}>
                        <Text style={styles.back}>Back</Text>
                    </TouchableOpacity>
                    <Text style={styles.title}>Diet Plan</Text>
                    <View style={{ width: 48 }} />
                </View>
                <View style={styles.emptyWrap}>
                    <Text style={styles.emptyText}>No diet plan found. Generate one from Home.</Text>
                </View>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()}>
                    <Text style={styles.back}>Back</Text>
                </TouchableOpacity>
                <Text style={styles.title}>Start Diet Plan</Text>
                <View style={{ width: 48 }} />
            </View>

            <ScrollView contentContainerStyle={styles.content}>
                <SurfaceCard style={styles.card}>
                    <Text style={styles.goal}>Goal: {plan.goal}</Text>
                    <Text style={styles.meta}>Hydration Target: {plan.hydration_target_liters}L/day</Text>
                    <Text style={styles.meta}>
                        Macros: {plan.macro_targets.calories} kcal | P {plan.macro_targets.protein_g}g | C {plan.macro_targets.carbs_g}g | F {plan.macro_targets.fats_g}g
                    </Text>
                </SurfaceCard>

                <Text style={styles.sectionTitle}>Meal Templates</Text>
                {plan.meal_templates.map((meal, idx) => (
                    <SurfaceCard style={styles.card} key={`${meal.meal_name}-${idx}`}>
                        <Text style={styles.mealTitle}>{meal.meal_name} ({meal.timing})</Text>
                        {meal.options.map((option, optionIdx) => (
                            <Text style={styles.line} key={`${meal.meal_name}-${optionIdx}`}>• {option}</Text>
                        ))}
                        {meal.notes ? <Text style={styles.note}>{meal.notes}</Text> : null}
                    </SurfaceCard>
                ))}

                <Text style={styles.sectionTitle}>Shopping Focus</Text>
                <SurfaceCard style={styles.card}>
                    {plan.shopping_focus.map((item, idx) => (
                        <Text key={`shop-${idx}`} style={styles.line}>• {item}</Text>
                    ))}
                </SurfaceCard>

                <Text style={styles.sectionTitle}>Adherence Tips</Text>
                <SurfaceCard style={styles.card}>
                    {plan.adherence_tips.map((tip, idx) => (
                        <Text key={`tip-${idx}`} style={styles.line}>• {tip}</Text>
                    ))}
                </SurfaceCard>
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
        paddingTop: 58,
        paddingBottom: 14,
        paddingHorizontal: 16,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottomWidth: 1,
        borderBottomColor: '#222222',
    },
    back: {
        color: '#93C5FD',
        fontSize: 16,
    },
    title: {
        color: '#F9FAFB',
        fontSize: 18,
        fontWeight: '700',
    },
    content: {
        padding: 16,
        paddingBottom: 28,
    },
    card: {
        padding: 14,
        marginBottom: 12,
    },
    goal: {
        color: '#F9FAFB',
        fontSize: 16,
        fontWeight: '700',
        marginBottom: 8,
    },
    meta: {
        color: '#D1D5DB',
        fontSize: 14,
        marginBottom: 6,
        lineHeight: 20,
    },
    sectionTitle: {
        color: '#E5E7EB',
        fontSize: 16,
        fontWeight: '700',
        marginTop: 8,
        marginBottom: 8,
    },
    mealTitle: {
        color: '#F3F4F6',
        fontSize: 15,
        fontWeight: '700',
        marginBottom: 6,
    },
    line: {
        color: '#D1D5DB',
        fontSize: 14,
        lineHeight: 21,
        marginBottom: 3,
    },
    note: {
        color: '#9CA3AF',
        fontSize: 13,
        marginTop: 4,
    },
    emptyWrap: {
        flex: 1,
        alignItems: 'center',
        justifyContent: 'center',
        paddingHorizontal: 20,
    },
    emptyText: {
        color: '#9CA3AF',
        fontSize: 15,
        textAlign: 'center',
    },
});
