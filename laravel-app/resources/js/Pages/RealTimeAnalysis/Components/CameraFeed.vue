<script setup>
import { ref, watch, onUnmounted, computed } from "vue";

// --- Props ---
const props = defineProps({
    deviceId: { type: String, default: null },
    autoScanEnabled: { type: Boolean, default: false },
    scanInterval: { type: Number, default: 1000 },
    detections: { type: Array, default: () => [] },
    sessionActive: { type: Boolean, default: false }, // ← ADDED: Session state control
});

// --- Emits ---
const emit = defineEmits([
    "capture",
    "frame-for-analysis",
    "started",
    "stopped",
]);

// --- Component Refs ---
const videoRef = ref(null);
const snapshotCanvasRef = ref(null);
const boundingBoxCanvasRef = ref(null);

// --- Component State ---
const stream = ref(null);
const isCameraActive = ref(false);
const isPaused = ref(false);
const errorMessage = ref("");
const scanTimer = ref(null);

// --- UPDATED: Now includes sessionActive condition ---
const isScanning = computed(
    () =>
        props.autoScanEnabled &&
        isCameraActive.value &&
        !isPaused.value &&
        props.sessionActive
    //                                                                        ↑ ADDED: Session must be active
);

// --- Drawing Logic ---
const drawBoundingBoxes = () => {
    const video = videoRef.value;
    const canvas = boundingBoxCanvasRef.value;
    if (!canvas || !video || !isCameraActive.value) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    props.detections.forEach((detection) => {
        const [x, y, w, h] = detection.bbox;
        const label = detection.label;
        ctx.strokeStyle =
            label.toLowerCase() === "product"
                ? "rgba(0, 255, 0, 0.8)"
                : "rgba(255, 0, 0, 0.8)";
        ctx.fillStyle = ctx.strokeStyle;
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, w, h);
        ctx.font = "16px Arial";
        const textWidth = ctx.measureText(label).width;
        ctx.fillRect(x, y - 20, textWidth + 10, 20);
        ctx.fillStyle = "#ffffff";
        ctx.fillText(label, x + 5, y - 5);
    });
};

watch(() => props.detections, drawBoundingBoxes, { deep: true });

// --- Core Camera Methods ---
const startDetection = async () => {
    if (stream.value) stopDetection(false); // Clean up previous stream silently

    errorMessage.value = "";
    const constraints = {
        video: {
            deviceId: props.deviceId ? { exact: props.deviceId } : undefined,
            width: { ideal: 1280 },
            height: { ideal: 720 },
        },
    };
    try {
        stream.value = await navigator.mediaDevices.getUserMedia(constraints);
        if (videoRef.value) {
            videoRef.value.srcObject = stream.value;
            videoRef.value.play();
            videoRef.value.onplay = () => {
                isCameraActive.value = true;
                isPaused.value = false;
                emit("started");
                drawBoundingBoxes();
                // NOTE: Scanning will only start when sessionActive becomes true
                // due to the updated isScanning computed property
            };
        }
    } catch (error) {
        console.error("Error accessing camera:", error);
        errorMessage.value =
            "Failed to access camera. Please check permissions.";
        isCameraActive.value = false;
    }
};

const stopDetection = (shouldEmit = true) => {
    stopScanLoop();
    if (stream.value) stream.value.getTracks().forEach((track) => track.stop());
    if (videoRef.value) videoRef.value.srcObject = null;
    const canvas = boundingBoxCanvasRef.value;
    if (canvas)
        canvas.getContext("2d").clearRect(0, 0, canvas.width, canvas.height);

    isCameraActive.value = false;
    isPaused.value = false; // Reset paused state on stop

    if (shouldEmit) {
        emit("stopped");
    }
};

// --- Capture & Scanning Logic ---
const pauseSession = () => {
    isPaused.value = true;
    stopScanLoop();
    console.log("Session paused.");
};

const resumeSession = () => {
    isPaused.value = false;
    startScanLoop();
    console.log("Session resumed.");
};

const saveAnalyzedFrame = async () => {
    return new Promise((resolve) => {
        if (!isCameraActive.value) {
            resolve(null);
            return;
        }
        const canvas = snapshotCanvasRef.value;
        const video = videoRef.value;
        const overlay = boundingBoxCanvasRef.value;
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        ctx.drawImage(overlay, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => resolve(blob), "image/jpeg");
    });
};

const startScanning = () => {
    // UPDATED: Check both camera AND session state
    if (
        isCameraActive.value &&
        !isPaused.value &&
        props.autoScanEnabled &&
        props.sessionActive
    ) {
        startScanLoop();
    }
};

defineExpose({
    saveAnalyzedFrame,
    resumeSession,
    pauseSession,
    startScanning,
    stopDetection,
});

const captureAndEmitForAnalysis = () => {
    // UPDATED: Additional safety check - don't capture if session not active
    if (!isCameraActive.value || isPaused.value || !props.sessionActive) {
        console.log("Skipping frame capture - session not active");
        return;
    }

    const canvas = snapshotCanvasRef.value;
    const video = videoRef.value;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(
        (blob) => {
            emit("frame-for-analysis", { blob, timestamp: new Date() });
        },
        "image/jpeg",
        0.85
    );
};

const startScanLoop = () => {
    stopScanLoop();
    // UPDATED: Additional check before starting loop
    if (
        props.autoScanEnabled &&
        props.scanInterval > 0 &&
        props.sessionActive
    ) {
        console.log("Starting scan loop - session is active");
        scanTimer.value = setInterval(
            captureAndEmitForAnalysis,
            props.scanInterval
        );
    } else {
        console.log(
            "Scan loop not started - session not active or auto-scan disabled"
        );
    }
};

const stopScanLoop = () => {
    if (scanTimer.value) {
        console.log("Stopping scan loop");
        clearInterval(scanTimer.value);
    }
    scanTimer.value = null;
};

// --- Watchers ---
// UPDATED: Now reacts to sessionActive changes too
watch(isScanning, (isNowScanning) => {
    console.log("isScanning changed:", isNowScanning);
    if (isNowScanning) {
        startScanLoop();
    } else {
        stopScanLoop();
    }
});

// UPDATED: Watch sessionActive prop changes
watch(
    () => props.sessionActive,
    (newSessionActive) => {
        console.log("sessionActive changed:", newSessionActive);
        if (
            newSessionActive &&
            isCameraActive.value &&
            props.autoScanEnabled &&
            !isPaused.value
        ) {
            console.log("Session became active - starting scan loop");
            startScanLoop();
        } else if (!newSessionActive) {
            console.log("Session became inactive - stopping scan loop");
            stopScanLoop();
        }
    }
);

watch(
    () => props.scanInterval,
    () => {
        if (isScanning.value) startScanLoop();
    }
);

watch(
    () => props.deviceId,
    (nv, ov) => {
        if (nv !== ov && isCameraActive.value) startDetection();
    }
);

onUnmounted(() => stopDetection(false));
</script>

<template>
    <div
        class="flex flex-col justify-center p-6 border border-gray-200 dark:border-dark-700 rounded-lg"
    >
        <!-- Header with Title and Action Buttons -->
        <div
            class="flex sm:flex-row flex-col justify-between items-center gap-3 mb-4"
        >
            <div class="flex gap-2">
                <h2
                    class="font-medium text-gray-800 dark:text-dark-100 text-base truncate tracking-wide"
                >
                    Camera Feed
                </h2>
                <!-- UPDATED: More specific live indicator -->
                <div v-if="isScanning" class="flex items-center gap-1 ml-4">
                    <span class="flex w-3 h-3">
                        <span
                            class="inline-flex absolute bg-red-400 opacity-75 rounded-full w-3 h-3 animate-ping"
                        ></span>
                        <span
                            class="inline-flex relative bg-red-500 rounded-full w-3 h-3"
                        ></span>
                    </span>
                    <span class="text-red-300 text-sm">Scanning...</span>
                </div>
                <!-- UPDATED: Show waiting state when camera active but session not ready -->
                <div
                    v-else-if="isCameraActive && !props.sessionActive"
                    class="flex items-center gap-1 ml-4"
                >
                    <span class="flex w-3 h-3">
                        <span
                            class="inline-flex relative bg-yellow-500 rounded-full w-3 h-3"
                        ></span>
                    </span>
                    <span class="text-yellow-300 text-sm"
                        >Waiting for session...</span
                    >
                </div>
            </div>
            <div class="flex space-x-2">
                <!-- Camera control buttons remain the same -->
                <button
                    v-if="!isCameraActive"
                    @click="startDetection"
                    class="gap-2 bg-this hover:bg-this-darker focus:bg-this-darker active:bg-this-darker/90 text-white btn-base btn this:success"
                >
                    <font-awesome-icon icon="fa-solid fa-play" />
                    Start Session
                </button>
                <button
                    v-else-if="!isPaused"
                    @click="pauseSession"
                    class="gap-2 bg-this hover:bg-this-darker focus:bg-this-darker active:bg-this-darker/90 text-white btn-base btn this:warning"
                >
                    <font-awesome-icon icon="fa-solid fa-pause" />
                    Pause Session
                </button>
                <button
                    v-else
                    @click="resumeSession"
                    class="gap-2 bg-this hover:bg-this-darker focus:bg-this-darker active:bg-this-darker/90 text-white btn-base btn this:success"
                >
                    <font-awesome-icon icon="fa-solid fa-play" />
                    Resume
                </button>

                <button
                    @click="stopDetection(true)"
                    :disabled="!isCameraActive"
                    class="gap-2 bg-this hover:bg-this-darker focus:bg-this-darker active:bg-this-darker/90 disabled:bg-this-light dark:disabled:bg-this-darker text-white btn-base btn this:error"
                >
                    <font-awesome-icon icon="fa-solid fa-stop" />
                    Stop Session
                </button>
            </div>
        </div>

        <!-- Video Display Area -->
        <div
            class="relative bg-black rounded-md w-full aspect-video overflow-hidden"
        >
            <video
                ref="videoRef"
                class="w-full h-full"
                muted
                playsinline
            ></video>

            <!-- Bounding Box Canvas Overlay -->
            <canvas
                ref="boundingBoxCanvasRef"
                class="top-0 left-0 absolute w-full h-full"
            >
            </canvas>

            <!-- Paused State Overlay -->
            <div
                v-if="isPaused"
                class="absolute inset-0 flex flex-col justify-center items-center bg-black bg-opacity-70 backdrop-blur-sm p-4 text-center"
            >
                <font-awesome-icon
                    icon="fa-solid fa-pause"
                    size="3x"
                    class="text-white"
                />
                <p class="mt-4 font-medium text-white text-2xl">
                    Session Paused
                </p>
            </div>

            <!-- UPDATED: Show waiting state overlay when camera active but session not ready -->
            <div
                v-else-if="isCameraActive && !props.sessionActive"
                class="absolute inset-0 flex flex-col justify-center items-center bg-blue-900 bg-opacity-70 backdrop-blur-sm p-4 text-center"
            >
                <font-awesome-icon
                    icon="fa-solid fa-clock"
                    size="3x"
                    class="text-blue-200"
                />
                <p class="mt-4 font-medium text-blue-100 text-2xl">
                    Waiting for Session
                </p>
                <p class="mt-2 text-blue-200 text-sm">
                    Camera ready - waiting for backend session to start
                </p>
            </div>

            <!-- Placeholder shown when the camera is off -->
            <div
                v-else-if="!isCameraActive"
                class="absolute inset-0 flex flex-col justify-center items-center bg-gray-200 dark:bg-dark-800 bg-opacity-80 p-4 text-center"
            >
                <font-awesome-icon icon="fa-solid fa-video-slash" size="2xl" />
                <p
                    class="mt-4 mb-2 font-medium text-gray-700 dark:text-dark-100 text-lg"
                >
                    Camera feed will appear here
                </p>
                <p v-if="!errorMessage">Click "Start Session" to begin</p>
                <p
                    v-if="errorMessage"
                    class="mt-2 max-w-md text-red-400 text-sm"
                >
                    {{ errorMessage }}
                </p>
            </div>
        </div>

        <!-- Hidden canvas used for capturing frames -->
        <canvas ref="snapshotCanvasRef" class="hidden"></canvas>
    </div>
</template>
