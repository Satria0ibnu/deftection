<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from "vue";
import { useForm } from "@inertiajs/vue3";
import axios from "axios";

// --- Import all the child components ---
import CameraFeed from "./Components/CameraFeed.vue";
import SessionControls from "./Components/SessionControls.vue";
import LiveStatistics from "./Components/LiveStatistics.vue";
import ScreenshotGallery from "./Components/ScreenshotGallery.vue";
import RecentDetections from "./Components/RecentDetections.vue";
import SessionEndModal from "./Components/Modals/SessionEndModal.vue";

// --- Component Refs ---
const cameraFeedRef = ref(null);

// --- Session Management State ---
const currentSession = ref(null);
const sessionLoading = ref(false);
const sessionError = ref(null);
const flaskApiStatus = ref(null);

// --- Session Configuration Form ---
const sessionForm = useForm({
    camera_location: "",
    session_config: {},
});

// --- State Management ---
const sessionConfig = reactive({
    selectedCameraId: null,
    scanInterval: 1500,
    autoCaptureEnabled: true,
});

const currentDetections = ref([]);
const stats = reactive({
    totalFrames: 0,
    goodProducts: 0,
    defectiveProducts: 0,
    screenshots: 0,
});
const allScreenshots = ref([]);

// --- Modal State ---
const isModalVisible = ref(false);
const modalState = ref("processing"); // 'processing' or 'finished'

// --- Session Management Functions ---
const startSession = async () => {
    sessionLoading.value = true;
    sessionError.value = null;

    try {
        // First check Flask API health before creating session
        console.log("Checking Flask AI health before starting session...");
        const healthResponse = await axios.get(
            `${
                import.meta.env.FLASK_API_URL || "http://localhost:5001"
            }/api/health`
        );

        if (!healthResponse.data || healthResponse.data.status !== "ok") {
            throw new Error(
                "Flask AI server is not healthy. Cannot start session."
            );
        }

        sessionForm.camera_location =
            sessionConfig.selectedCameraId || "Default Camera";
        sessionForm.session_config = {
            scanInterval: sessionConfig.scanInterval,
            autoCaptureEnabled: sessionConfig.autoCaptureEnabled,
        };

        const response = await axios.post(route("realtime.sessions.start"), {
            camera_location: sessionForm.camera_location,
            session_config: sessionForm.session_config,
        });

        const data = response.data;

        if (data.success) {
            currentSession.value = data.session;
            flaskApiStatus.value = data.flask_api;
            resetSession();
            console.log("Session started successfully:", data.message);
            console.log("Session ID:", data.session.id);
        } else {
            throw new Error(data.message || "Failed to start session");
        }
    } catch (error) {
        sessionError.value = error.response?.data?.message || error.message;
        console.error("Error starting session:", error);

        // If health check fails, show specific error
        if (error.message.includes("Flask AI server")) {
            sessionError.value =
                "AI Detection Server is offline. Please check the Flask AI service.";
        }
    } finally {
        sessionLoading.value = false;
    }
};

const pauseSession = async () => {
    if (!currentSession.value) return;

    sessionLoading.value = true;
    try {
        const response = await axios.post("/api/realtime/sessions/pause");
        currentSession.value = response.data.session;
        console.log("Session paused successfully");
    } catch (error) {
        sessionError.value = error.response?.data?.message || error.message;
    } finally {
        sessionLoading.value = false;
    }
};

const resumeSession = async () => {
    if (!currentSession.value) return;

    sessionLoading.value = true;
    try {
        // Check Flask health before resuming
        console.log("Checking Flask AI health before resuming session...");
        const healthResponse = await axios.get(
            `${
                import.meta.env.VITE_FLASK_API_URL || "http://localhost:5001"
            }/api/health`
        );

        if (!healthResponse.data || healthResponse.data.status !== "healthy") {
            throw new Error(
                "Flask AI server is not healthy. Cannot resume session."
            );
        }

        const response = await axios.post("/api/realtime/sessions/resume");
        currentSession.value = response.data.session;
        console.log("Session resumed successfully");
    } catch (error) {
        sessionError.value = error.response?.data?.message || error.message;

        if (error.message.includes("Flask AI server")) {
            sessionError.value =
                "AI Detection Server is offline. Session cannot be resumed.";
        }
    } finally {
        sessionLoading.value = false;
    }
};

const stopSession = async () => {
    console.log("stopSession called");
    console.log("Current session:", currentSession.value);

    if (!currentSession.value) {
        console.warn("No session to stop");
        return;
    }

    sessionLoading.value = true;
    sessionError.value = null;

    try {
        console.log("Sending stop request...");

        const response = await axios.post("/api/realtime/sessions/stop");

        console.log("Stop response:", response);
        console.log("Stop response data:", response.data);

        const data = response.data;

        if (data.success) {
            const completedSession = data.session;
            currentSession.value = null;

            // Update modal with final session stats
            modalState.value = "finished";
            isModalVisible.value = true;

            console.log("Session stopped successfully:", data.message);
            console.log("Final Session Stats:", completedSession);
        } else {
            throw new Error(data.message || "Failed to stop session");
        }
    } catch (error) {
        console.error("Error stopping session:", error);
        console.error("Error response:", error.response);
        console.error("Error response data:", error.response?.data);

        sessionError.value = error.response?.data?.message || error.message;

        // If it's a 404, it means no session was found - clear the current session
        if (error.response?.status === 404) {
            console.log("Session not found, clearing current session");
            currentSession.value = null;
        }
    } finally {
        sessionLoading.value = false;
    }
};

const getCurrentSession = async () => {
    try {
        const response = await axios.get(route("realtime.sessions.current"));
        currentSession.value = response.data.session;

        if (response.data.session) {
            console.log("Found existing session:", response.data.session.id);
            stats.totalFrames = response.data.session.total_frames_processed;
            stats.goodProducts = response.data.session.good_count;
            stats.defectiveProducts = response.data.session.defect_count;
        }
    } catch (error) {
        console.error("Error getting current session:", error);
    }
};

// --- Computed Properties ---
const detectionRate = computed(() => {
    if (stats.totalFrames === 0) return 0;
    return stats.defectiveProducts / stats.totalFrames;
});

const recentDetections = computed(() => {
    return allScreenshots.value.filter((s) => s.type === "Defect").slice(0, 5);
});

const sessionDuration = computed(() => {
    if (!currentSession.value) return "00:00:00";

    const start = new Date(currentSession.value.session_start);
    const now = new Date();
    const diff = Math.floor((now - start) / 1000);

    const hours = Math.floor(diff / 3600);
    const minutes = Math.floor((diff % 3600) / 60);
    const seconds = diff % 60;

    return `${hours.toString().padStart(2, "0")}:${minutes
        .toString()
        .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
});

const isSessionActive = computed(() => {
    return (
        currentSession.value && currentSession.value.session_status === "active"
    );
});

const isSessionPaused = computed(() => {
    return (
        currentSession.value && currentSession.value.session_status === "paused"
    );
});

const hasActiveOrPausedSession = computed(() => {
    return (
        currentSession.value &&
        ["active", "paused"].includes(currentSession.value.session_status)
    );
});

const sessionStatusColor = computed(() => {
    if (!currentSession.value) return "";

    switch (currentSession.value.session_status) {
        case "active":
            return "text-green-600";
        case "paused":
            return "text-yellow-600";
        case "completed":
            return "text-blue-600";
        case "aborted":
            return "text-red-600";
        default:
            return "text-gray-600";
    }
});

const sessionStatusText = computed(() => {
    if (!currentSession.value) return "";

    switch (currentSession.value.session_status) {
        case "active":
            return "Active Session";
        case "paused":
            return "Paused Session";
        case "completed":
            return "Completed Session";
        case "aborted":
            return "Aborted Session";
        default:
            return "Unknown Status";
    }
});

// --- Main Analysis Logic (updated with session tracking) ---
const handleFrameForAnalysis = async (frameData) => {
    // Only process if we have an active session
    console.log("Current session:", currentSession.value);
    console.log("Session status:", currentSession.value?.session_status);
    console.log("Is session active:", isSessionActive.value);

    if (!hasActiveOrPausedSession.value) {
        console.warn("No active session - frame analysis skipped");
        return;
    }

    try {
        console.log("Sending frame blob directly to Laravel backend...");

        // Create FormData with the blob directly (faster than base64)
        const formData = new FormData();
        formData.append("frame_blob", frameData.blob, "frame.jpg");
        formData.append("session_id", currentSession.value.id);
        formData.append("timestamp", frameData.timestamp.toISOString());

        // Call the real API endpoint with multipart data
        const response = await axios.post(
            route("realtime.sessions.process_frame"),
            formData,
            {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            }
        );

        // LOG THE COMPLETE RESPONSE
        console.log("=== COMPLETE LARAVEL RESPONSE ===");
        console.log("Response status:", response.status);
        console.log("Response headers:", response.headers);
        console.log("Response data:", response.data);
        console.log("=== END RESPONSE ===");

        const apiResponse = response.data;

        if (apiResponse.success) {
            console.log("Frame analysis successful:", {
                status: apiResponse.status,
                anomaly_score: apiResponse.anomaly_score,
                processing_time: apiResponse.processing_time,
            });

            // LOG THE DETECTION RESULTS
            console.log("=== DETECTION RESULTS ===");
            console.log("Detections array:", apiResponse.detections);
            console.log("Session stats:", apiResponse.session_stats);
            console.log("=== END DETECTION RESULTS ===");

            // Update detection data for bounding box display
            currentDetections.value = apiResponse.detections || [];

            // Wait for the next frame to ensure boxes are drawn
            await new Promise((resolve) => requestAnimationFrame(resolve));

            // Get screenshot with overlay for local display
            if (cameraFeedRef.value) {
                const blobWithOverlay =
                    await cameraFeedRef.value.saveAnalyzedFrame();

                if (blobWithOverlay) {
                    // Update local stats based on real API response
                    stats.totalFrames = apiResponse.session_stats.total_frames;
                    stats.goodProducts = apiResponse.session_stats.good_count;
                    stats.defectiveProducts =
                        apiResponse.session_stats.defect_count;

                    // Add screenshot to local display
                    const screenshotType =
                        apiResponse.status === "defect" ? "Defect" : "Good";
                    addScreenshot(
                        blobWithOverlay,
                        screenshotType,
                        frameData.timestamp
                    );

                    // Log processing performance
                    const totalProcessingTime = Object.values(
                        apiResponse.processing_time || {}
                    ).reduce((a, b) => a + b, 0);
                    if (totalProcessingTime > 0) {
                        console.log(
                            `Frame processed in ${totalProcessingTime.toFixed(
                                3
                            )}s`
                        );
                    }
                }
            }

            // Clear bounding boxes after display time
            setTimeout(() => {
                currentDetections.value = [];
            }, 2500);
        } else {
            console.error("Frame analysis failed:", apiResponse);
            sessionError.value =
                "Frame analysis failed. Check connection to AI server.";
        }
    } catch (error) {
        console.error("=== ERROR PROCESSING FRAME ===");
        console.error("Error object:", error);
        console.error("Error response:", error.response);
        console.error("Error response data:", error.response?.data);
        console.error("Error response status:", error.response?.status);
        console.error("=== END ERROR ===");

        // Handle different types of errors gracefully
        if (error.response?.status === 403) {
            sessionError.value =
                "Not authorized to process frames for this session.";
        } else if (error.response?.status === 400) {
            sessionError.value =
                "Session is not active. Cannot process frames.";
        } else if (error.response?.status === 500) {
            sessionError.value = "AI detection server error. Please try again.";
        } else if (error.response?.status === 429) {
            console.warn("Rate limit hit, slowing down frame processing");
            return;
        } else {
            sessionError.value = "Network error. Check your connection.";
        }

        // Clear any existing detections on error
        currentDetections.value = [];
    }
};

// --- Event Handlers (updated with session management) ---
const handleDetectionStarted = async () => {
    console.log("Detection starting...");

    // First check if we have a paused session and resume it
    if (isSessionPaused.value) {
        console.log(
            "Session is paused. Resuming session:",
            currentSession.value.id
        );
        await resumeSession();
        // After resuming, start scanning
        if (cameraFeedRef.value) {
            cameraFeedRef.value.startScanning();
        }
    }
    // Only start new session if we don't have any session at all
    else if (!hasActiveOrPausedSession.value) {
        console.log("No session exists. Starting new session...");
        await startSession();
        // Only start scanning AFTER session is successfully created
        if (isSessionActive.value && cameraFeedRef.value) {
            cameraFeedRef.value.startScanning();
        }
    }
    // If we already have an active session, just start scanning
    else if (isSessionActive.value && cameraFeedRef.value) {
        cameraFeedRef.value.startScanning();
    }
};

const handleDetectionStopped = async () => {
    console.log("Detection stopped. Current session:", currentSession.value);
    console.log("Is session active?", isSessionActive.value);

    if (isSessionActive.value || isSessionPaused.value) {
        isModalVisible.value = true;
        modalState.value = "processing";

        // Simulate a delay for processing the session report
        setTimeout(async () => {
            console.log("Processing timeout reached, calling stopSession");
            try {
                await stopSession();
            } catch (error) {
                console.error("=== ERROR STOPPING SESSION ===");
                console.error("Error message:", error.message);
                console.error("Error response status:", error.response?.status);
                console.error("Error response data:", error.response?.data);
                console.error(
                    "Error response headers:",
                    error.response?.headers
                );
                console.error("Full error object:", error);
                console.error("=== END ERROR ===");

                sessionError.value =
                    error.response?.data?.message || error.message;

                // Show the actual error message to user
                if (error.response?.data?.message) {
                    console.log(
                        "Laravel error message:",
                        error.response.data.message
                    );
                    sessionError.value = error.response.data.message;
                } else if (error.response?.data?.error) {
                    console.log("Laravel error:", error.response.data.error);
                    sessionError.value = error.response.data.error;
                }

                // If it's a 404, it means no session was found - clear the current session
                if (error.response?.status === 404) {
                    console.log("Session not found, clearing current session");
                    currentSession.value = null;
                }
            }
        }, 2000); // 2-second delay
    } else {
        console.log("No active/paused session, just showing modal");
        // If no active session, just show the modal with current stats
        isModalVisible.value = true;
        modalState.value = "finished";
    }
};

const handleManualCapture = (screenshotData) => {
    addScreenshot(screenshotData.blob, "Manual", screenshotData.timestamp);
};

// --- Modal Action Handlers ---
const handleStartNewSession = async () => {
    resetSession();
    isModalVisible.value = false;
    await startSession();
};

const handleViewDetails = () => {
    console.log("Navigating to session details page...");
    // Navigate to session history or details page
    window.location.href = "/analysis/session-history";
};

// --- Helper Functions ---
const addScreenshot = (blob, type, timestamp) => {
    const screenshot = {
        id: `${type}-${timestamp.getTime()}`,
        url: URL.createObjectURL(blob),
        timestamp: timestamp,
        type: type,
    };
    allScreenshots.value.unshift(screenshot);
    stats.screenshots++;
};

const resetSession = () => {
    stats.totalFrames = 0;
    stats.goodProducts = 0;
    stats.defectiveProducts = 0;
    stats.screenshots = 0;
    allScreenshots.value.forEach((img) => URL.revokeObjectURL(img.url));
    allScreenshots.value = [];
    currentDetections.value = [];
    isModalVisible.value = false;
    sessionError.value = null;
    console.log("Session stats have been reset.");
};

// --- Lifecycle hooks ---
onMounted(async () => {
    // Check for existing active session on page load
    await getCurrentSession();
});

onUnmounted(() => {
    // Clean up screenshot URLs
    allScreenshots.value.forEach((img) => URL.revokeObjectURL(img.url));
});
</script>

<template>
    <!-- Main Content -->
    <div class="relative w-full">
        <div class="gap-6 grid grid-cols-1 lg:grid-cols-3">
            <!-- Main Content: Camera Feed -->
            <div class="lg:col-span-2">
                <CameraFeed
                    ref="cameraFeedRef"
                    :device-id="sessionConfig.selectedCameraId"
                    :auto-scan-enabled="sessionConfig.autoCaptureEnabled"
                    :scan-interval="sessionConfig.scanInterval"
                    :detections="currentDetections"
                    :session-active="isSessionActive"
                    @frame-for-analysis="handleFrameForAnalysis"
                    @capture="handleManualCapture"
                    @started="handleDetectionStarted"
                    @stopped="handleDetectionStopped"
                />
            </div>

            <!-- Sidebar: Controls and Stats -->
            <div class="flex flex-col justify-between">
                <LiveStatistics
                    :total-frames="stats.totalFrames"
                    :good-products="stats.goodProducts"
                    :defective-products="stats.defectiveProducts"
                    :detection-rate="detectionRate"
                    :screenshots="stats.screenshots"
                    :session-duration="sessionDuration"
                    :session-id="currentSession?.id"
                />

                <div
                    class="bg-gray-200 dark:bg-dark-500 max-2xl:my-6 h-px"
                ></div>

                <SessionControls
                    :session-active="isSessionActive"
                    :session-loading="sessionLoading"
                    @update:cameraId="
                        (id) => (sessionConfig.selectedCameraId = id)
                    "
                    @update:scanInterval="
                        (val) => (sessionConfig.scanInterval = val)
                    "
                    @update:autoCapture="
                        (val) => (sessionConfig.autoCaptureEnabled = val)
                    "
                    @reset-stats="resetSession"
                    @start-session="startSession"
                    @pause-session="pauseSession"
                    @resume-session="resumeSession"
                    @stop-session="stopSession"
                />
            </div>
        </div>

        <!-- Screenshot Gallery & Recent Detections -->
        <div class="gap-6 grid grid-cols-1 lg:grid-cols-3 mt-6">
            <RecentDetections :detections="recentDetections" />
            <div class="lg:col-span-2">
                <ScreenshotGallery
                    :screenshots="allScreenshots"
                    @clear-all="resetSession"
                />
            </div>
        </div>

        <!-- Session End Modal -->
        <SessionEndModal
            :is-visible="isModalVisible"
            :state="modalState"
            :stats="stats"
            :session="currentSession"
            @start-new="handleStartNewSession"
            @view-details="handleViewDetails"
            @close="isModalVisible = false"
        />
    </div>
</template>
