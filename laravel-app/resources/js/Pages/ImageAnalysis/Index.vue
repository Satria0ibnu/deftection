<script setup>
// Imports
import { ref, computed, watch } from "vue";
import { router, useForm } from "@inertiajs/vue3";

import ImageSelector from "./Components/ImageSelector.vue";
import ImageTabs from "./Components/ImageTabs.vue";
import BatchImageSelector from "./Components/BatchImageSelector.vue";
import ProcessingModal from "./Components/Modals/ProcessingModal.vue";
import SuccessModal from "./Components/Modals/SuccessModal.vue";

import { successToast } from "@/utils/swal.js"; // Make sure this path is correct

const props = defineProps({
    scanResult: {
        type: Object,
        required: false,
        default: null,
    },
});

console.log("ImageAnalysis props:", props);

watch(
    () => props.scanResult,
    (newResults) => {
        if (newResults) {
            detectionResult.value = newResults;
            console.log("Scan results updated:", newResults);
        }
    }
);

// View Mode State (Single vs Batch)
const isBatchMode = ref(false);
const handleSwitchMode = (mode) => {
    isBatchMode.value = mode === "batch";
    detectionResult.value = null;
};

// Single Image Analysis State
const selectedFile = ref(null);
const detectionResult = ref(null);
const loading = ref(false);

// Inertia form for single image
const form = useForm({
    image: null,
});

// Handle file selection for single image mode
const handleFileSelected = (file) => {
    selectedFile.value = file;
    form.image = file;

    // Reset result if file is cleared
    if (!file) {
        detectionResult.value = null;
    }
    console.log("File selected:", file);
};

// Original image preview URL for ImageTabs.vue
const originalUrl = computed(() => {
    return selectedFile.value ? URL.createObjectURL(selectedFile.value) : null;
});

// Run single image analysis (mocked async)
async function handleRunAnalysis(settings) {
    if (!selectedFile.value) return alert("Please select a file first.");

    loading.value = true;
    detectionResult.value = null;

    form.image = selectedFile.value;

    form.post(route("scans.store"), {
        forceFormData: true,
        preserveScroll: true,
        onSuccess: () => {
            console.log("Analysis completed successfully.");
            successToast("Analysis completed successfully!");
        },
        onError: (errors) => {
            console.error("Analysis failed:", errors);
            alert("Analysis failed. Please try again.");
        },
    });

    loading.value = false;
}

// Batch Analysis State
const isProcessing = ref(false);
const isSuccess = ref(false);
const processedCount = ref(0);
const totalCount = ref(0);

// Run batch analysis (simulated per file)
async function handleRunBatchAnalysis(files) {
    isProcessing.value = true;
    isSuccess.value = false;
    processedCount.value = 0;
    totalCount.value = files.length;

    // 1. Send all files at once to the new 'startBatch' route
    files.forEach((fileWrapper, index) => {
        // Access the actual file using fileWrapper.file
        const file = fileWrapper.file; // <-- Get the nested File object

        if (file) {
            console.log(
                `File ${index}: ${file.name}, Size: ${(
                    file.size / 1024
                ).toFixed(2)} KB`
            );
            if (file.size / 1024 > 4096) {
                console.error(
                    `---> ERROR: File ${file.name} is larger than the 4MB limit!`
                );
            }
        } else {
            console.error(`File object at index ${index} is undefined.`);
        }
    });

    // Also update your FormData append line
    const formData = new FormData();
    files.forEach((fileWrapper) => {
        // Make sure to append the actual file object
        formData.append("images[]", fileWrapper.file);
    });

    try {
        const response = await axios.post(route("scans.store.batch"), formData);
        console.log("Batch analysis started successfully:", response.data);
        const batchId = response.data.batch_id;

        // 2. Start polling for status updates
        const intervalId = setInterval(async () => {
            try {
                const statusResponse = await axios.get(
                    route("scans.batch.status", { batchId })
                );
                const { processed, total } = statusResponse.data;

                processedCount.value = processed;
                totalCount.value = total;

                console.log(`Batch status: ${processed}/${total} processed`);

                // 3. Stop polling when the job is done
                if (total > 0 && processed >= total) {
                    clearInterval(intervalId);
                    isProcessing.value = false;
                    isSuccess.value = true;
                }
            } catch (error) {
                console.error("Failed to get batch status:", error);
                clearInterval(intervalId);
                isProcessing.value = false;
                // Handle error state
            }
        }, 100); // Check every 0.5 seconds
    } catch (error) {
        console.error("Failed to start batch:", error);
        isProcessing.value = false;
        // Handle error state
    }
}

// Retry batch analysis (reset everything)
const batchRef = ref(null);
function resetBatch() {
    isSuccess.value = false;
    processedCount.value = 0;
    totalCount.value = 0;

    // Call the exposed method in BatchImageSelector.vue
    batchRef.value?.clearFiles();
}

// URL of processed detection image for ImageTabs.vue
const detectionUrl = computed(() => {
    return props.scanResult ? props.scanResult.annotatedImageUrl : null;
});
</script>

<template>
    <div
        v-if="!isBatchMode"
        class="flex lg:flex-row flex-col gap-6 w-full h-fit"
    >
        <div class="flex flex-col gap-6 w-full lg:w-xl">
            <ImageSelector
                :loading="loading"
                @file-selected="handleFileSelected"
                @run-analysis="handleRunAnalysis"
                @switch-mode="handleSwitchMode"
            />
        </div>
        <div class="flex flex-col flex-1">
            <ImageTabs
                :original-url="originalUrl"
                :detection-url="detectionUrl"
                :show-steps="true"
                :has-run-analysis="!!detectionResult"
                :detectionResult="detectionResult"
            />
        </div>
    </div>

    <div v-else>
        <BatchImageSelector
            ref="batchRef"
            :loading="loading"
            @run-batch-analysis="handleRunBatchAnalysis"
            @switch-mode="handleSwitchMode"
        />
    </div>

    <!-- Modal for batch -->
    <ProcessingModal
        :visible="isProcessing"
        :current="processedCount"
        :total="totalCount"
    />

    <SuccessModal
        :visible="isSuccess"
        :total="totalCount"
        @retry="resetBatch"
    />
</template>
