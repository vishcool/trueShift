import React, { ReactNode } from 'react';
import { StyleSheet, Text, View } from 'react-native';

interface MessageBubbleProps {
    role: 'user' | 'agent';
    text: string;
    label?: string;
    footer?: ReactNode;
}

export function MessageBubble({ role, text, label, footer }: MessageBubbleProps) {
    const isUser = role === 'user';

    return (
        <View style={[styles.row, isUser ? styles.userRow : styles.agentRow]}>
            <View style={[styles.bubble, isUser ? styles.userBubble : styles.agentBubble]}>
                {label ? <Text style={[styles.label, isUser ? styles.userLabel : styles.agentLabel]}>{label}</Text> : null}
                <Text style={[styles.text, isUser ? styles.userText : styles.agentText]}>{text}</Text>
            </View>
            {footer}
        </View>
    );
}

const styles = StyleSheet.create({
    row: {
        marginBottom: 12,
    },
    userRow: {
        alignItems: 'flex-end',
    },
    agentRow: {
        alignItems: 'flex-start',
    },
    bubble: {
        maxWidth: '90%',
        paddingHorizontal: 14,
        paddingVertical: 11,
        borderRadius: 16,
    },
    userBubble: {
        backgroundColor: '#2563EB',
        borderBottomRightRadius: 5,
    },
    agentBubble: {
        backgroundColor: '#171717',
        borderWidth: 1,
        borderColor: '#2F2F2F',
        borderBottomLeftRadius: 5,
    },
    label: {
        fontSize: 11,
        marginBottom: 4,
        fontWeight: '700',
    },
    userLabel: {
        color: '#E5EDFF',
    },
    agentLabel: {
        color: '#9CA3AF',
    },
    text: {
        fontSize: 15,
        lineHeight: 21,
    },
    userText: {
        color: '#FFFFFF',
    },
    agentText: {
        color: '#E5E7EB',
    },
});
