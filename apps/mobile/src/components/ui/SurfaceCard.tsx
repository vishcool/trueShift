import React, { ReactNode } from 'react';
import { StyleSheet, View, ViewStyle } from 'react-native';

interface SurfaceCardProps {
    children: ReactNode;
    style?: ViewStyle;
}

export function SurfaceCard({ children, style }: SurfaceCardProps) {
    return <View style={[styles.card, style]}>{children}</View>;
}

const styles = StyleSheet.create({
    card: {
        backgroundColor: '#131313',
        borderWidth: 1,
        borderColor: '#2C2C2C',
        borderRadius: 16,
    },
});
