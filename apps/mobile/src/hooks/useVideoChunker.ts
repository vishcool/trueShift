import { useState, useRef, useCallback, useEffect } from 'react';
import { CameraView } from 'expo-camera';
import { api } from '../api/client';

export const useVideoChunker = () => {
    const cameraRef = useRef<CameraView>(null);
    const [isRecording, setIsRecording] = useState(false);
    const isRecordingRef = useRef(false); // Ref for the loop

    const [sessionId, setSessionId] = useState<string | null>(null);
    const [lastFeedback, setLastFeedback] = useState<string | null>(null);

    // Chunk processing logic
    const processChunk = async (uri: string, currentIdx: number, currentSessionId: string) => {
        try {
            const formData = new FormData();
            formData.append('file', {
                uri,
                name: `chunk_${currentIdx}.mp4`,
                type: 'video/mp4',
            } as any);
            formData.append('session_id', currentSessionId);
            formData.append('chunk_index', String(currentIdx));

            console.log(`[Vision] Uploading chunk ${currentIdx}...`);
            const response = await api.vision.analyzeChunk(formData);

            if (response.data?.data) {
                const { feedback, form_score } = response.data.data;
                setLastFeedback(`${feedback} (Score: ${Math.round(form_score)})`);
                console.log(`[Vision] Feedback: ${feedback}`);
            }
        } catch (error) {
            console.error("[Vision] Failed to upload chunk:", error);
        }
    };

    const startRecording = useCallback(async () => {
        if (!cameraRef.current) return;

        const newSessionId = Date.now().toString();
        setSessionId(newSessionId);
        setIsRecording(true);
        isRecordingRef.current = true;
        setLastFeedback("Starting analysis...");

        let currentIdx = 0;

        // Loop function
        const recordLoop = async () => {
            if (!isRecordingRef.current || !cameraRef.current) return;

            try {
                console.log(`[Vision] Recording chunk ${currentIdx}...`);
                const promise = cameraRef.current.recordAsync({
                    maxDuration: 3, // Stop automatically after 3s
                });

                const data = await promise;

                // If stopped manually mid-recording, data might be returned.
                // Check if we are still "conceptually" recording to process it.
                if (isRecordingRef.current && data?.uri) {
                    // Upload in background (don't await to keep loop tight? 
                    // actually better to await slightly or just fire and forget but 
                    // we don't want to choke network. Let's fire and forget for MVP)
                    processChunk(data.uri, currentIdx, newSessionId);
                    currentIdx++;

                    // Recursive call to continue loop
                    // Small delay to ensure camera is ready? usually recordAsync is enough.
                    recordLoop();
                } else if (!isRecordingRef.current) {
                    console.log("[Vision] Loop stopped manually.");
                }

            } catch (e) {
                console.warn("[Vision] Recording error", e);
                setIsRecording(false);
                isRecordingRef.current = false;
            }
        };

        // Start the loop
        recordLoop();

    }, []);

    const stopRecording = useCallback(() => {
        console.log("[Vision] Stopping recording...");
        setIsRecording(false);
        isRecordingRef.current = false;
        if (cameraRef.current) {
            cameraRef.current.stopRecording();
        }
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (isRecordingRef.current) {
                stopRecording();
            }
        };
    }, []);

    return {
        cameraRef,
        isRecording,
        startRecording,
        stopRecording,
        lastFeedback
    };
};
