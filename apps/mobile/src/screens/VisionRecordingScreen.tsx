import React, { useEffect, useState } from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CameraView, useCameraPermissions, useMicrophonePermissions } from 'expo-camera';
import { useVideoChunker } from '../hooks/useVideoChunker';

export default function VisionRecordingScreen({ navigation }: any) {
    const [cameraPermission, requestCameraPermission] = useCameraPermissions();
    const [micPermission, requestMicPermission] = useMicrophonePermissions();
    const { cameraRef, isRecording, startRecording, stopRecording, lastFeedback } = useVideoChunker();

    useEffect(() => {
        if (!cameraPermission) requestCameraPermission();
        if (!micPermission) requestMicPermission();
    }, [cameraPermission, micPermission]);

    if (!cameraPermission || !micPermission) {
        return <View style={styles.container} />;
    }

    if (!cameraPermission.granted || !micPermission.granted) {
        return (
            <View style={styles.container}>
                <Text style={{ color: 'white', textAlign: 'center', marginTop: 50 }}>
                    Camera and Audio permissions are required
                </Text>
                <TouchableOpacity onPress={() => { requestCameraPermission(); requestMicPermission(); }} style={{ marginTop: 20, padding: 10, backgroundColor: 'white', alignSelf: 'center', borderRadius: 5 }}>
                    <Text>Grant Permissions</Text>
                </TouchableOpacity>
            </View>
        );
    }

    return (
        <View style={styles.container}>
            <CameraView
                ref={cameraRef}
                style={StyleSheet.absoluteFill}
                facing="front"
                mode="video"
            />
            <SafeAreaView style={styles.overlay} pointerEvents="box-none">
                {/* Header */}
                <View style={styles.header}>
                    <TouchableOpacity onPress={() => navigation.goBack()} style={styles.closeBtn}>
                        <Text>Close</Text>
                    </TouchableOpacity>
                    <Text style={styles.headerTitle}>AI Form Coach</Text>
                </View>

                {/* Feedback Area */}
                <View style={styles.feedbackContainer}>
                    {lastFeedback ? (
                        <View style={styles.feedbackBox}>
                            <Text style={styles.feedbackText}>{lastFeedback}</Text>
                        </View>
                    ) : isRecording ? (
                        <Text style={styles.statusText}>Analyzing...</Text>
                    ) : (
                        <Text style={styles.statusText}>Align yourself and press Start</Text>
                    )}
                </View>

                {/* Controls */}
                <View style={styles.controls}>
                    <TouchableOpacity
                        style={[
                            styles.recordButton,
                            isRecording ? styles.recording : styles.idle
                        ]}
                        onPress={isRecording ? stopRecording : startRecording}
                    >
                        <View style={styles.recordInner} />
                    </TouchableOpacity>
                </View>
            </SafeAreaView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: 'black',
    },
    camera: {
        flex: 1,
    },
    overlay: {
        ...StyleSheet.absoluteFillObject,
        justifyContent: 'space-between',
        padding: 20,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
    },
    closeBtn: {
        padding: 10,
        backgroundColor: 'rgba(0,0,0,0.5)',
        borderRadius: 20,
    },
    headerTitle: {
        color: 'white',
        fontSize: 18,
        fontWeight: 'bold',
        marginLeft: 15,
        textShadowColor: 'rgba(0,0,0,0.75)',
        textShadowOffset: { width: -1, height: 1 },
        textShadowRadius: 10
    },
    feedbackContainer: {
        alignItems: 'center',
        justifyContent: 'center',
        flex: 1,
    },
    feedbackBox: {
        backgroundColor: 'rgba(0, 255, 0, 0.3)', // Greenish tint
        padding: 20,
        borderRadius: 15,
        borderWidth: 2,
        borderColor: '#00FF00',
    },
    feedbackText: {
        color: 'white',
        fontSize: 24,
        fontWeight: 'bold',
        textAlign: 'center',
        textShadowColor: 'black',
        textShadowRadius: 5,
    },
    statusText: {
        color: 'rgba(255,255,255,0.8)',
        fontSize: 18,
        textAlign: 'center',
    },
    controls: {
        alignItems: 'center',
        marginBottom: 30,
    },
    recordButton: {
        width: 80,
        height: 80,
        borderRadius: 40,
        borderWidth: 6,
        borderColor: 'white',
        alignItems: 'center',
        justifyContent: 'center',
    },
    idle: {
        borderColor: 'white',
    },
    recording: {
        borderColor: 'red',
    },
    recordInner: {
        width: 60,
        height: 60,
        borderRadius: 30,
        backgroundColor: 'red',
    }
});
