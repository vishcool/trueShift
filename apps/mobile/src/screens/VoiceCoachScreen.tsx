import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Platform, ScrollView } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';
const { EncodingType, cacheDirectory } = FileSystem;
import { api } from '../api/client';
import { useAuth } from '../hooks/useAuth';

export default function VoiceCoachScreen() {
    const navigation = useNavigation();
    const { user } = useAuth();

    // State
    const [status, setStatus] = useState<'idle' | 'recording' | 'processing' | 'speaking' | 'error'>('idle');
    const [transcript, setTranscript] = useState('');
    const [agentResponse, setAgentResponse] = useState('');
    const [errorMessage, setErrorMessage] = useState('');

    // Refs
    const wsRef = useRef<WebSocket | null>(null);
    const recordingRef = useRef<Audio.Recording | null>(null);
    const soundRef = useRef<Audio.Sound | null>(null);
    const stopRecordingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    // Initialize WebSocket
    useEffect(() => {
        if (!user) return;

        // Request microphone permission up front
        (async () => {
            const permission = await Audio.requestPermissionsAsync();
            if (permission.status !== 'granted') {
                setErrorMessage('Microphone permission is required to use Voice Coach.');
            }
        })();

        const ws = api.voice.createSocket(user.id);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('[VoiceCoach] WebSocket connected');
        };

        ws.onmessage = async (e) => {
            try {
                const data = JSON.parse(e.data);

                if (data.type === 'transcript') {
                    setTranscript(data.text);
                } else if (data.type === 'agent_text') {
                    setAgentResponse(data.text);
                } else if (data.type === 'state') {
                    setStatus(data.status); // processing, speaking, idle
                } else if (data.type === 'audio_out') {
                    // Play the base64 audio
                    await playBase64Audio(data.data);
                } else if (data.type === 'error') {
                    setStatus('error');
                    setErrorMessage(data.message);
                }
            } catch (err) {
                console.error('[VoiceCoach] Ws msg parse error', err);
            }
        };

        ws.onclose = () => {
            console.log('[VoiceCoach] WebSocket closed');
            setStatus('idle');
        };

        return () => {
            ws.close();
            cleanupAudio();
        };
    }, [user]);

    const cleanupAudio = async () => {
        if (recordingRef.current) {
            await recordingRef.current.stopAndUnloadAsync();
        }
        if (soundRef.current) {
            await soundRef.current.unloadAsync();
        }
    };

    const playBase64Audio = async (base64String: string) => {
        try {
            // Unload previous
            if (soundRef.current) {
                await soundRef.current.unloadAsync();
            }

            const tempUri = cacheDirectory + `temp_agent_voice_${Date.now()}.wav`;
            await FileSystem.writeAsStringAsync(tempUri, base64String, {
                encoding: EncodingType.Base64,
            });

            await Audio.setAudioModeAsync({
                allowsRecordingIOS: false,
                playsInSilentModeIOS: true,
                staysActiveInBackground: false,
            });

            const { sound } = await Audio.Sound.createAsync(
                { uri: tempUri },
                { shouldPlay: true }
            );

            soundRef.current = sound;

            sound.setOnPlaybackStatusUpdate((playbackStatus) => {
                if ('didJustFinish' in playbackStatus && playbackStatus.didJustFinish) {
                    setStatus('idle');
                }
            });

        } catch (error) {
            console.error('[VoiceCoach] Playback error', error);
            setStatus('idle');
        }
    };

    const startRecording = async () => {
        try {
            // Stop TTS if playing
            if (soundRef.current) {
                await soundRef.current.stopAsync();
            }

            // Cleanup any existing recording object to prevent duplicate preparations
            if (recordingRef.current) {
                try {
                    await recordingRef.current.stopAndUnloadAsync();
                } catch (e) {
                    // Ignore unload errors if it was already unloaded
                }
                recordingRef.current = null;
            }

            setTranscript('...');
            setAgentResponse('');
            setErrorMessage('');
            setStatus('recording');

            // Request permission
            const permission = await Audio.requestPermissionsAsync();
            if (permission.status !== 'granted') {
                setStatus('error');
                setErrorMessage('Microphone permission denied');
                return;
            }

            await Audio.setAudioModeAsync({
                allowsRecordingIOS: true,
                playsInSilentModeIOS: true,
                staysActiveInBackground: false,
            });

            const recording = new Audio.Recording();
            await recording.prepareToRecordAsync({
                isMeteringEnabled: true,
                android: {
                    extension: '.wav',
                    outputFormat: Audio.AndroidOutputFormat.MPEG_4,
                    audioEncoder: Audio.AndroidAudioEncoder.AAC,
                    sampleRate: 16000,
                    numberOfChannels: 1,
                    bitRate: 128000,
                },
                ios: {
                    extension: '.wav',
                    audioQuality: Audio.IOSAudioQuality.HIGH,
                    sampleRate: 16000,
                    numberOfChannels: 1,
                    bitRate: 128000,
                    linearPCMBitDepth: 16,
                    linearPCMIsBigEndian: false,
                    linearPCMIsFloat: false,
                },
                web: {
                    mimeType: 'audio/webm',
                    bitsPerSecond: 128000,
                },
            });

            await recording.startAsync();
            recordingRef.current = recording;

            // To prevent hanging indefinitely, force stop after 30s
            stopRecordingTimeoutRef.current = setTimeout(() => {
                if (status === 'recording') {
                    stopRecording();
                }
            }, 30000);

        } catch (err) {
            console.error('[VoiceCoach] Failed to start recording', err);
            setStatus('error');
            setErrorMessage('Failed to access microphone');
        }
    };

    const stopRecording = async () => {
        if (!recordingRef.current || status !== 'recording') return;

        if (stopRecordingTimeoutRef.current) {
            clearTimeout(stopRecordingTimeoutRef.current);
        }

        try {
            setStatus('processing');
            const recording = recordingRef.current;
            recordingRef.current = null;

            let uri = null;
            try {
                const recStatus = await recording.getStatusAsync();
                // Ensure it's not already unloaded/not prepared
                if (recStatus.canRecord || recStatus.isRecording) {
                    await recording.stopAndUnloadAsync();
                }
                // We can always attempt to get the URI even if it hasn't actually recorded much, 
                // but if it errors getting URI we catch it safely.
                uri = recording.getURI();
            } catch (e) {
                console.warn('[VoiceCoach] Recorder not fully initialized before stopping', e);
            }

            if (uri && wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                // Read file as base64
                const base64Audio = await FileSystem.readAsStringAsync(uri, {
                    encoding: EncodingType.Base64,
                });

                // Send as single chunk to backend
                wsRef.current.send(JSON.stringify({ type: 'audio', data: base64Audio }));
                wsRef.current.send(JSON.stringify({ type: 'stop' }));
            } else {
                // E.g. user tapped incredibly fast or network is down
                setStatus('idle');
            }

        } catch (error) {
            console.error('[VoiceCoach] Stop recording error', error);
            setStatus('error');
        }
    };

    const getStatusText = () => {
        switch (status) {
            case 'idle': return 'Hold to speak';
            case 'recording': return 'Listening...';
            case 'processing': return 'Thinking...';
            case 'speaking': return 'Agent is speaking...';
            case 'error': return 'Error (Try again)';
            default: return '';
        }
    };

    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
                    <Text style={styles.backButtonText}>← Back</Text>
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Voice Coach</Text>
                <View style={{ width: 50 }} />
            </View>

            {/* Conversation Area */}
            <ScrollView style={styles.convoArea} contentContainerStyle={styles.convoContent}>

                {/* User Transcript */}
                {(transcript || status === 'recording') && (
                    <View style={styles.userBubble}>
                        <Text style={styles.userLabel}>You</Text>
                        <Text style={styles.userText}>{transcript}</Text>
                        {status === 'recording' && <ActivityIndicator size="small" color="#fff" style={{ marginTop: 5, alignSelf: 'flex-start' }} />}
                    </View>
                )}

                {/* Agent Reply */}
                {agentResponse ? (
                    <View style={styles.agentBubble}>
                        <Text style={styles.agentLabel}>AI Coach</Text>
                        <Text style={styles.agentText}>{agentResponse}</Text>
                        {status === 'speaking' && <ActivityIndicator size="small" color="#6366F1" style={{ marginTop: 5, alignSelf: 'flex-start' }} />}
                    </View>
                ) : null}

                {status === 'processing' && !agentResponse && (
                    <ActivityIndicator size="large" color="#6366F1" style={{ marginTop: 40 }} />
                )}

                {errorMessage ? (
                    <Text style={styles.errorText}>{errorMessage}</Text>
                ) : null}

            </ScrollView>

            {/* Mic Control */}
            <View style={styles.controlsArea}>
                <Text style={styles.statusText}>{getStatusText()}</Text>

                <TouchableOpacity
                    style={[
                        styles.micButton,
                        status === 'recording' ? styles.micRecording : null,
                        status === 'processing' ? styles.micDisabled : null
                    ]}
                    onPressIn={startRecording}
                    onPressOut={stopRecording}
                    disabled={status === 'processing' || status === 'speaking'}
                    activeOpacity={0.7}
                >
                    <View style={status === 'recording' ? styles.micInnerRecording : styles.micInner} />
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
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        paddingTop: 60,
        paddingHorizontal: 20,
        paddingBottom: 20,
        borderBottomWidth: 1,
        borderBottomColor: '#222',
    },
    backButton: {
        padding: 5,
        width: 50,
    },
    backButtonText: {
        color: '#FFFFFF',
        fontSize: 14,
    },
    headerTitle: {
        color: '#FFFFFF',
        fontSize: 18,
        fontWeight: 'bold',
    },
    convoArea: {
        flex: 1,
    },
    convoContent: {
        padding: 24,
        paddingBottom: 100,
    },
    userBubble: {
        alignSelf: 'flex-end',
        maxWidth: '85%',
        backgroundColor: '#1F1F1F',
        padding: 16,
        borderRadius: 16,
        borderBottomRightRadius: 4,
        marginBottom: 24,
    },
    userLabel: {
        color: '#888',
        fontSize: 12,
        marginBottom: 4,
        fontWeight: 'bold',
    },
    userText: {
        color: '#FFF',
        fontSize: 18,
        lineHeight: 26,
    },
    agentBubble: {
        alignSelf: 'flex-start',
        maxWidth: '85%',
        padding: 8,
        marginBottom: 24,
    },
    agentLabel: {
        color: '#6366F1',
        fontSize: 12,
        marginBottom: 8,
        fontWeight: 'bold',
    },
    agentText: {
        color: '#FFF',
        fontSize: 20,
        lineHeight: 28,
        fontWeight: '500',
    },
    controlsArea: {
        height: 180,
        justifyContent: 'center',
        alignItems: 'center',
        borderTopWidth: 1,
        borderTopColor: '#222',
        backgroundColor: '#0A0A0A',
    },
    statusText: {
        color: '#888',
        fontSize: 14,
        marginBottom: 20,
    },
    errorText: {
        color: '#EF4444',
        fontSize: 14,
        textAlign: 'center',
        marginTop: 20,
    },
    micButton: {
        width: 80,
        height: 80,
        borderRadius: 40,
        backgroundColor: '#1F1F1F',
        justifyContent: 'center',
        alignItems: 'center',
        borderWidth: 2,
        borderColor: '#333',
    },
    micRecording: {
        borderColor: '#EF4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        transform: [{ scale: 1.1 }],
    },
    micDisabled: {
        opacity: 0.5,
    },
    micInner: {
        width: 32,
        height: 32,
        borderRadius: 16,
        backgroundColor: '#6366F1',
    },
    micInnerRecording: {
        width: 24,
        height: 24,
        borderRadius: 4,
        backgroundColor: '#EF4444',
    }
});
