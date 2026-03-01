import React from 'react';
import { StyleSheet, Text, TouchableOpacity, ViewStyle } from 'react-native';

interface ActionChipProps {
    label: string;
    onPress: () => void;
    active?: boolean;
    style?: ViewStyle;
}

export function ActionChip({ label, onPress, active = false, style }: ActionChipProps) {
    return (
        <TouchableOpacity onPress={onPress} style={[styles.chip, active && styles.chipActive, style]}>
            <Text style={[styles.text, active && styles.textActive]}>{label}</Text>
        </TouchableOpacity>
    );
}

const styles = StyleSheet.create({
    chip: {
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderRadius: 12,
        borderWidth: 1,
        borderColor: '#2C2C2C',
        backgroundColor: '#141414',
    },
    chipActive: {
        backgroundColor: '#242424',
        borderColor: '#4B5563',
    },
    text: {
        color: '#D1D5DB',
        fontSize: 12,
        fontWeight: '600',
    },
    textActive: {
        color: '#F9FAFB',
    },
});
