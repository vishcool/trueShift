import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
    ActivityIndicator,
    FlatList,
    StyleSheet,
    Switch,
    Text,
    TouchableOpacity,
    View,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system';

import { api, VoicePreferences } from '../api/client';
import { useAuth } from '../hooks/useAuth';
import { ActionChip } from '../components/ui/ActionChip';
import { MessageBubble } from '../components/ui/MessageBubble';
import { SurfaceCard } from '../components/ui/SurfaceCard';

type VoiceStatus = 'idle' | 'recording' | 'processing' | 'speaking' | 'error';
type VoiceMode = 'general' | 'workout' | 'diet' | 'recovery';

interface VoiceTurn {
    id: string;
    userText?: string;
    coachText?: string;
}

const MODES: Array<{ id: VoiceMode; label: string }> = [
    { id: 'general', label: 'Coach' },
    { id: 'workout', label: 'Workout' },
    { id: 'diet', label: 'Diet' },
    { id: 'recovery', label: 'Recovery' },
];

const LANGUAGES = [
    { label: 'EN', code: 'en-IN' },
    { label: 'HI', code: 'hi-IN' },
    { label: 'TA', code: 'ta-IN' },
    { label: 'ML', code: 'ml-IN' },
];

const VOICES = [
    { label: 'Meera', value: 'meera' },
    { label: 'Aarav', value: 'aarav' },
];

function createTurn(userText?: string, coachText?: string): VoiceTurn {
    return {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        userText,
        coachText,
    };
}

export default function VoiceCoachScreen() {
    const navigation = useNavigation<any>();
    const route = useRoute<any>();
    const { user } = useAuth();

    const [status, setStatus] = useState<VoiceStatus>('idle');
    const [errorMessage, setErrorMessage] = useState('');
    const [selectedMode, setSelectedMode] = useState<VoiceMode>(route.params?.initialMode || 'general');
    const [selectedLanguage, setSelectedLanguage] = useState('en-IN');
    const [selectedVoice, setSelectedVoice] = useState('meera');
    const [ttsEnabled, setTtsEnabled] = useState(true);
    const [turns, setTurns] = useState<VoiceTurn[]>([]);
    const [voiceSessionId, setVoiceSessionId] = useState(`voice-${Date.now()}`);
    const [isLoadingPrefs, setIsLoadingPrefs] = useState(true);

    const wsRef = useRef<WebSocket | null>(null);
    const recordingRef = useRef<Audio.Recording | null>(null);
    const soundRef = useRef<Audio.Sound | null>(null);
    const chunkTimerRef = useRef<NodeJS.Timeout | null>(null);
    const segmentBusyRef = useRef(false);
    const isRecordingSessionRef = useRef(false);
    const chunkSeqRef = useRef(0);
    const pendingTranscriptRef = useRef<string>('');

    const userSocketId = useMemo(() => user?.firebase_uid || user?.id, [user?.firebase_uid, user?.id]);

    const syncVoicePreferences = useCallback(async (updates: Partial<VoicePreferences>) => {
        try {
            await api.voice.updatePreferences(updates);
        } catch {
            // best-effort
        }
    }, []);

    useEffect(() => {
        let mounted = true;
        const loadPreferences = async () => {
            if (!userSocketId) {
                return;
            }
            setIsLoadingPrefs(true);
            try {
                const res = await api.voice.getPreferences();
                if (!mounted) {
                    return;
                }
                setSelectedLanguage(res.data.preferred_language_code);
                setSelectedVoice(res.data.preferred_voice);
                setSelectedMode(route.params?.initialMode || res.data.default_mode);
                setTtsEnabled(res.data.tts_enabled);
            } catch {
                // keep defaults
            } finally {
                if (mounted) {
                    setIsLoadingPrefs(false);
                }
            }
        };
        loadPreferences();

        return () => {
            mounted = false;
        };
    }, [route.params?.initialMode, userSocketId]);

    const sendSocketContext = useCallback(() => {
        if (wsRef.current?.readyState !== WebSocket.OPEN) {
            return;
        }

        wsRef.current.send(
            JSON.stringify({
                type: 'context',
                mode: selectedMode,
                language_code: selectedLanguage,
                voice: selectedVoice,
                tts_enabled: ttsEnabled,
            })
        );
    }, [selectedLanguage, selectedMode, selectedVoice, ttsEnabled]);

    const cleanupAudio = useCallback(async () => {
        if (chunkTimerRef.current) {
            clearInterval(chunkTimerRef.current);
            chunkTimerRef.current = null;
        }

        if (recordingRef.current) {
            try {
                await recordingRef.current.stopAndUnloadAsync();
            } catch {
                // no-op
            }
            recordingRef.current = null;
        }

        if (soundRef.current) {
            try {
                await soundRef.current.unloadAsync();
            } catch {
                // no-op
            }
            soundRef.current = null;
        }

        isRecordingSessionRef.current = false;
        segmentBusyRef.current = false;
    }, []);

    const playBase64Audio = useCallback(async (base64Audio: string) => {
        try {
            if (soundRef.current) {
                await soundRef.current.unloadAsync();
            }

            const cacheDirectory = (FileSystem as any).cacheDirectory as string;
            const tempFile = `${cacheDirectory}voice-coach-${Date.now()}.wav`;
            await (FileSystem as any).writeAsStringAsync(tempFile, base64Audio, { encoding: 'base64' });

            await Audio.setAudioModeAsync({
                allowsRecordingIOS: false,
                playsInSilentModeIOS: true,
                staysActiveInBackground: false,
            });

            const { sound } = await Audio.Sound.createAsync({ uri: tempFile }, { shouldPlay: true });
            soundRef.current = sound;

            sound.setOnPlaybackStatusUpdate((playbackState) => {
                if ('didJustFinish' in playbackState && playbackState.didJustFinish) {
                    setStatus('idle');
                }
            });
        } catch {
            setStatus('error');
            setErrorMessage('Failed to play coach audio output.');
        }
    }, []);

    useEffect(() => {
        if (!userSocketId || isLoadingPrefs) {
            return;
        }

        let mounted = true;

        const setup = async () => {
            const permission = await Audio.requestPermissionsAsync();
            if (permission.status !== 'granted' && mounted) {
                setStatus('error');
                setErrorMessage('Microphone permission is required for voice coaching.');
                return;
            }

            const socket = api.voice.createSocket(userSocketId, {
                mode: selectedMode,
                language_code: selectedLanguage,
                voice: selectedVoice,
                tts_enabled: ttsEnabled,
                session_id: voiceSessionId,
            });
            wsRef.current = socket;

            socket.onopen = () => {
                sendSocketContext();
            };

            socket.onmessage = async (event) => {
                try {
                    const data = JSON.parse(event.data);

                    if (data.type === 'status' && data.session_id) {
                        setVoiceSessionId(data.session_id);
                    } else if (data.type === 'transcript') {
                        pendingTranscriptRef.current = data.text || '';
                    } else if (data.type === 'agent_text') {
                        const newTurn = createTurn(pendingTranscriptRef.current, data.text || '');
                        pendingTranscriptRef.current = '';
                        setTurns(prev => [newTurn, ...prev]);
                    } else if (data.type === 'state') {
                        setStatus(data.status || 'idle');
                    } else if (data.type === 'audio_out') {
                        await playBase64Audio(data.data);
                    } else if (data.type === 'error') {
                        setStatus('error');
                        setErrorMessage(data.message || 'Voice coach failed to process audio.');
                    }
                } catch {
                    setStatus('error');
                    setErrorMessage('Invalid response from voice service.');
                }
            };

            socket.onclose = () => {
                if (mounted) {
                    setStatus('idle');
                }
            };
        };

        setup();

        return () => {
            mounted = false;
            wsRef.current?.close();
            cleanupAudio();
        };
    }, [cleanupAudio, isLoadingPrefs, playBase64Audio, selectedLanguage, selectedMode, selectedVoice, sendSocketContext, ttsEnabled, userSocketId, voiceSessionId]);

    useEffect(() => {
        sendSocketContext();
        syncVoicePreferences({
            preferred_language_code: selectedLanguage,
            preferred_voice: selectedVoice,
            default_mode: selectedMode,
            tts_enabled: ttsEnabled,
        });
    }, [selectedLanguage, selectedMode, selectedVoice, sendSocketContext, syncVoicePreferences, ttsEnabled]);

    const startSegmentRecording = useCallback(async () => {
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
    }, []);

    const flushCurrentSegment = useCallback(async () => {
        if (!recordingRef.current || wsRef.current?.readyState !== WebSocket.OPEN) {
            return;
        }

        const recording = recordingRef.current;
        recordingRef.current = null;

        try {
            await recording.stopAndUnloadAsync();
        } catch {
            return;
        }

        const uri = recording.getURI();
        if (!uri) {
            return;
        }

        const audioBase64 = await (FileSystem as any).readAsStringAsync(uri, { encoding: 'base64' });
        if (!audioBase64 || audioBase64.length < 1000) {
            return;
        }

        chunkSeqRef.current += 1;
        wsRef.current.send(
            JSON.stringify({
                type: 'audio_chunk',
                data: audioBase64,
                seq: chunkSeqRef.current,
            })
        );
    }, []);

    const rotateSegment = useCallback(async () => {
        if (!isRecordingSessionRef.current || segmentBusyRef.current) {
            return;
        }

        segmentBusyRef.current = true;
        try {
            await flushCurrentSegment();
            if (isRecordingSessionRef.current) {
                await startSegmentRecording();
            }
        } finally {
            segmentBusyRef.current = false;
        }
    }, [flushCurrentSegment, startSegmentRecording]);

    const startRecording = useCallback(async () => {
        try {
            if (wsRef.current?.readyState !== WebSocket.OPEN) {
                setErrorMessage('Voice socket not connected yet.');
                return;
            }

            setErrorMessage('');

            if (soundRef.current) {
                await soundRef.current.stopAsync();
            }

            await cleanupAudio();

            await Audio.setAudioModeAsync({
                allowsRecordingIOS: true,
                playsInSilentModeIOS: true,
                staysActiveInBackground: false,
            });

            isRecordingSessionRef.current = true;
            chunkSeqRef.current = 0;
            setStatus('recording');

            wsRef.current.send(JSON.stringify({ type: 'start', session_id: voiceSessionId }));
            await startSegmentRecording();

            chunkTimerRef.current = setInterval(() => {
                rotateSegment();
            }, 1200);
        } catch {
            setStatus('error');
            setErrorMessage('Could not start microphone recording.');
        }
    }, [cleanupAudio, rotateSegment, startSegmentRecording, voiceSessionId]);

    const stopRecording = useCallback(async () => {
        if (!isRecordingSessionRef.current) {
            return;
        }

        try {
            isRecordingSessionRef.current = false;
            if (chunkTimerRef.current) {
                clearInterval(chunkTimerRef.current);
                chunkTimerRef.current = null;
            }

            await flushCurrentSegment();

            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: 'stop' }));
            }

            setStatus('processing');
        } catch {
            setStatus('error');
            setErrorMessage('Could not process recorded audio.');
        }
    }, [flushCurrentSegment]);

    const toggleRecording = useCallback(async () => {
        if (status === 'processing' || status === 'speaking') {
            return;
        }

        if (status === 'recording') {
            await stopRecording();
            return;
        }

        await startRecording();
    }, [startRecording, status, stopRecording]);

    const getStatusText = () => {
        if (status === 'idle') return 'Tap mic to start live streaming';
        if (status === 'recording') return 'Streaming chunks... tap again to stop';
        if (status === 'processing') return 'Processing your voice...';
        if (status === 'speaking') return 'Coach is replying...';
        return 'Voice error';
    };

    return (
        <View style={styles.container}>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()} style={styles.navBtn}>
                    <Text style={styles.navBtnText}>Back</Text>
                </TouchableOpacity>
                <Text style={styles.headerTitle}>Voice Coach</Text>
                <View style={styles.navSpacer} />
            </View>

            <View style={styles.modeRow}>
                {MODES.map((mode) => (
                    <ActionChip
                        key={mode.id}
                        label={mode.label}
                        active={selectedMode === mode.id}
                        onPress={() => setSelectedMode(mode.id)}
                        style={styles.flexChip}
                    />
                ))}
            </View>

            <View style={styles.langRow}>
                {LANGUAGES.map((lang) => (
                    <ActionChip
                        key={lang.code}
                        label={lang.label}
                        active={selectedLanguage === lang.code}
                        onPress={() => setSelectedLanguage(lang.code)}
                    />
                ))}
            </View>

            <View style={styles.voiceRow}>
                {VOICES.map((voice) => (
                    <ActionChip
                        key={voice.value}
                        label={voice.label}
                        active={selectedVoice === voice.value}
                        onPress={() => setSelectedVoice(voice.value)}
                    />
                ))}
                <SurfaceCard style={styles.ttsCard}>
                    <Text style={styles.ttsLabel}>TTS</Text>
                    <Switch
                        value={ttsEnabled}
                        onValueChange={setTtsEnabled}
                        trackColor={{ false: '#244A40', true: '#2A7E68' }}
                        thumbColor="#FFFFFF"
                    />
                </SurfaceCard>
            </View>

            <FlatList
                data={turns}
                keyExtractor={(item) => item.id}
                style={styles.turnList}
                contentContainerStyle={styles.turnListContent}
                ListEmptyComponent={<Text style={styles.emptyText}>Start speaking to begin a segmented voice session.</Text>}
                renderItem={({ item }) => (
                    <View>
                        {item.userText ? <MessageBubble role="user" label="You" text={item.userText} /> : null}
                        {item.coachText ? <MessageBubble role="agent" label="Coach" text={item.coachText} /> : null}
                    </View>
                )}
            />

            <View style={styles.controls}>
                <Text style={styles.statusText}>{getStatusText()}</Text>
                <Text style={styles.sessionText}>Session: {voiceSessionId}</Text>

                <TouchableOpacity
                    style={[
                        styles.micBtn,
                        status === 'recording' && styles.micBtnRecording,
                        (status === 'processing' || status === 'speaking' || isLoadingPrefs) && styles.micBtnDisabled,
                    ]}
                    onPress={toggleRecording}
                    disabled={status === 'processing' || status === 'speaking' || isLoadingPrefs}
                >
                    {status === 'processing' ? (
                        <ActivityIndicator size="small" color="#FFFFFF" />
                    ) : (
                        <Text style={styles.micBtnText}>{status === 'recording' ? 'Stop' : 'Talk'}</Text>
                    )}
                </TouchableOpacity>

                {errorMessage ? <Text style={styles.errorText}>{errorMessage}</Text> : null}
            </View>
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
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottomWidth: 1,
        borderBottomColor: '#222222',
    },
    navBtn: {
        width: 60,
    },
    navBtnText: {
        color: '#93C5FD',
        fontSize: 14,
    },
    navSpacer: {
        width: 60,
    },
    headerTitle: {
        color: '#F9FAFB',
        fontSize: 18,
        fontWeight: '700',
    },
    modeRow: {
        flexDirection: 'row',
        marginTop: 12,
        paddingHorizontal: 12,
        gap: 8,
    },
    flexChip: {
        flex: 1,
        alignItems: 'center',
    },
    langRow: {
        flexDirection: 'row',
        paddingHorizontal: 14,
        marginTop: 10,
        gap: 8,
    },
    voiceRow: {
        flexDirection: 'row',
        paddingHorizontal: 14,
        marginTop: 10,
        gap: 8,
        alignItems: 'center',
    },
    ttsCard: {
        marginLeft: 'auto',
        flexDirection: 'row',
        alignItems: 'center',
        paddingHorizontal: 10,
        paddingVertical: 6,
        gap: 8,
    },
    ttsLabel: {
        color: '#D1D5DB',
        fontSize: 12,
        fontWeight: '600',
    },
    turnList: {
        flex: 1,
        marginTop: 10,
    },
    turnListContent: {
        paddingHorizontal: 14,
        paddingBottom: 14,
    },
    emptyText: {
        color: '#9CA3AF',
        fontSize: 13,
        textAlign: 'center',
        marginTop: 40,
    },
    controls: {
        borderTopWidth: 1,
        borderTopColor: '#222222',
        paddingVertical: 14,
        alignItems: 'center',
        paddingHorizontal: 16,
    },
    statusText: {
        color: '#9CA3AF',
        fontSize: 12,
        marginBottom: 4,
    },
    sessionText: {
        color: '#6B7280',
        fontSize: 11,
        marginBottom: 10,
    },
    micBtn: {
        width: 94,
        height: 94,
        borderRadius: 47,
        backgroundColor: '#2563EB',
        justifyContent: 'center',
        alignItems: 'center',
        borderWidth: 2,
        borderColor: '#60A5FA',
    },
    micBtnRecording: {
        backgroundColor: '#B44545',
        borderColor: '#DB7B7B',
    },
    micBtnDisabled: {
        opacity: 0.55,
    },
    micBtnText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: '700',
    },
    errorText: {
        color: '#F38F8F',
        marginTop: 12,
        textAlign: 'center',
        fontSize: 12,
    },
});
