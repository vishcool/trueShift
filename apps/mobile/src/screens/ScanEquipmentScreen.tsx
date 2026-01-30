import React, { useState, useRef } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator, Alert } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useNavigation } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { api } from '../api/client';

export default function ScanEquipmentScreen() {
    const navigation = useNavigation<any>();
    const [permission, requestPermission] = useCameraPermissions();
    const cameraRef = useRef<CameraView>(null);
    const [isAnalyzing, setIsAnalyzing] = useState(false);

    if (!permission) {
        // Camera permissions are still loading.
        return <View />;
    }

    if (!permission.granted) {
        return (
            <View style={styles.container}>
                <Text style={styles.message}>We need your permission to show the camera</Text>
                <TouchableOpacity onPress={requestPermission} style={styles.permissionButton}>
                    <Text style={styles.permissionButtonText}>Grant Permission</Text>
                </TouchableOpacity>
            </View>
        );
    }

    const takePictureAndAnalyze = async () => {
        if (cameraRef.current && !isAnalyzing) {
            try {
                setIsAnalyzing(true);
                const photo = await cameraRef.current.takePictureAsync({
                    quality: 0.7,
                    base64: false, // We use URI
                });

                if (!photo) throw new Error("Failed to take photo");

                // Call API
                const response = await api.workout.generateWithVision(photo, {
                    duration_minutes: 45, // Defaults
                    fitness_level: "Intermediate"
                });

                // Navigate to Vision Screen or Workout Display
                // Assuming we want to show the plan first, but for now let's go straight to Vision tracking akin to startWorkout in WorkoutGenScreen
                // Or better, go hack to WorkoutGenScreen but with the plan data populated.

                // For this MVP, let's navigate to WorkoutGenScreen and pass the plan.
                // However, WorkoutGenScreen might need updates to accept params.
                // Alternatively, go directly to Vision if ready. 
                // Let's assume we want to review it.

                navigation.navigate('WorkoutGen', { generatedPlan: response.data });

            } catch (error) {
                console.error(error);
                Alert.alert("Error", "Failed to analyze equipment. Please try again.");
            } finally {
                setIsAnalyzing(false);
            }
        }
    };

    return (
        <View style={styles.container}>
            <CameraView style={styles.camera} facing="back" ref={cameraRef}>
                <SafeAreaView style={styles.overlay}>
                    <View style={styles.header}>
                        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
                            <Text style={styles.backButtonText}>Cancel</Text>
                        </TouchableOpacity>
                        <Text style={styles.headerText}>Scan Equipment</Text>
                    </View>

                    <View style={styles.footer}>
                        <Text style={styles.instructionText}>
                            Point at available equipment (dumbbells, bench, etc.) or an empty space.
                        </Text>

                        <TouchableOpacity
                            style={[styles.captureButton, isAnalyzing && styles.disabledButton]}
                            onPress={takePictureAndAnalyze}
                            disabled={isAnalyzing}
                        >
                            {isAnalyzing ? (
                                <ActivityIndicator color="#000" size="large" />
                            ) : (
                                <View style={styles.captureInner} />
                            )}
                        </TouchableOpacity>
                    </View>
                </SafeAreaView>
            </CameraView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: 'black',
    },
    message: {
        textAlign: 'center',
        paddingBottom: 10,
        color: 'white',
    },
    camera: {
        flex: 1,
    },
    overlay: {
        flex: 1,
        justifyContent: 'space-between',
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 20,
        backgroundColor: 'rgba(0,0,0,0.3)',
    },
    backButton: {
        padding: 5,
    },
    backButtonText: {
        color: 'white',
        fontSize: 16,
    },
    headerText: {
        color: 'white',
        fontSize: 18,
        fontWeight: 'bold',
        marginLeft: 20,
    },
    footer: {
        padding: 30,
        alignItems: 'center',
        backgroundColor: 'rgba(0,0,0,0.5)',
    },
    instructionText: {
        color: '#DDD',
        textAlign: 'center',
        marginBottom: 30,
        fontSize: 16,
    },
    captureButton: {
        width: 80,
        height: 80,
        borderRadius: 40,
        backgroundColor: 'white',
        justifyContent: 'center',
        alignItems: 'center',
    },
    captureInner: {
        width: 70,
        height: 70,
        borderRadius: 35,
        borderWidth: 2,
        borderColor: '#000',
        backgroundColor: 'white',
    },
    disabledButton: {
        opacity: 0.7,
    },
    permissionButton: {
        backgroundColor: '#6366F1',
        padding: 15,
        borderRadius: 10,
        alignSelf: 'center',
    },
    permissionButtonText: {
        color: 'white',
        fontWeight: 'bold',
    },
});
