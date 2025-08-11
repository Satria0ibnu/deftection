// Add these changes to your RealTimeAnalysis/Index.vue

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
        sessionForm.camera_location =
            sessionConfig.selectedCameraId || "Default Camera";
        sessionForm.session_config = {
            scanInterval: sessionConfig.scanInterval,
            autoCaptureEnabled: sessionConfig.autoCaptureEnabled,
        };

        const response = await axios.post("/api/realtime/sessions/start", {
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
        const response = await axios.post("/api/realtime/sessions/resume");
        currentSession.value = response.data.session;
        console.log("Session resumed successfully");
    } catch (error) {
        sessionError.value = error.response?.data?.message || error.message;
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
        const response = await axios.get("/api/realtime/sessions/current");
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
    if (!isSessionActive.value) {
        console.warn("No active session - frame analysis skipped");
        return;
    }

    // 1. Simulate API call
    const fakeApiResponse = await simulateApiCall();

    // 2. Pass detection data down to CameraFeed to draw the boxes
    currentDetections.value = fakeApiResponse.detections;

    // 3. Wait for the next frame to ensure boxes are drawn
    await new Promise((resolve) => requestAnimationFrame(resolve));

    // 4. Call the child component to get a NEW screenshot that includes the overlay
    if (cameraFeedRef.value) {
        const blobWithOverlay = await cameraFeedRef.value.saveAnalyzedFrame();

        if (blobWithOverlay) {
            // 5. Process the result using the NEW blob
            stats.totalFrames++;
            if (fakeApiResponse.status === "good") {
                stats.goodProducts++;
                addScreenshot(blobWithOverlay, "Good", frameData.timestamp);
            } else if (fakeApiResponse.status === "defected") {
                stats.defectiveProducts++;
                addScreenshot(blobWithOverlay, "Defect", frameData.timestamp);
            }

            // 6. Here you would also send this data to your backend to update the session
            // updateSessionStats();
        }
    }

    // 7. Clear bounding boxes after a delay
    setTimeout(() => {
        currentDetections.value = [];
    }, 2500);
};

const simulateApiCall = () => {
    return new Promise((resolve) => {
        setTimeout(() => {
            const isDefect = Math.random() > 0.6; // 40% chance of defect
            resolve({
                status: isDefect ? "defected" : "good",
                detections: isDefect
                    ? [
                          { label: "Product", bbox: [150, 200, 400, 250] },
                          { label: "Scratch", bbox: [250, 280, 150, 20] },
                      ]
                    : [{ label: "Product", bbox: [150, 200, 400, 250] }],
            });
        }, 500); // Simulate 500ms network latency
    });
};

// --- Event Handlers (updated with session management) ---
const handleDetectionStarted = async () => {
    console.log("Detection starting...");

    if (!isSessionActive.value) {
        console.log("No active session. Starting new session...");
        await startSession();
    }

    if (isSessionActive.value) {
        console.log(
            "Detection started with active session:",
            currentSession.value.id
        );
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
            await stopSession();
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
