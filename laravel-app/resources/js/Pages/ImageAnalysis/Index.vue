<script setup>
import { ref, computed, watch } from "vue";
import { router, useForm } from "@inertiajs/vue3";
import axios from "axios";
import ImageSelector from "./Components/ImageSelector.vue";
import ImageTabs from "./Components/ImageTabs.vue";
import BatchImageSelector from "./Components/BatchImageSelector.vue";
import ProcessingModal from "./Components/Modals/ProcessingModal.vue";
import SuccessModal from "./Components/Modals/SuccessModal.vue";
import { successToast, errorToast } from "@/utils/swal.js";

// --- Props ---
const props = defineProps({
    scanResult: {
        type: Object,
        required: false,
        default: null,
    },
});

// --- Component Mode (Single vs. Batch) ---
const isBatchMode = ref(false);

const handleSwitchMode = (mode) => {
    isBatchMode.value = mode === "batch";
    detectionResult.value = null;
};

// --- Single Image Analysis ---
const selectedFile = ref(null);
const detectionResult = ref(props.scanResult);
const loading = ref(false);
const form = useForm({ image: null });

const originalUrl = computed(() => {
    return selectedFile.value ? URL.createObjectURL(selectedFile.value) : null;
});

// Provides the URL of the processed/annotated image to the child component.
const detectionUrl = computed(() =>
    props.scanResult ? props.scanResult.annotatedImageUrl : null
);

const handleFileSelected = (file) => {
    selectedFile.value = file;
    form.image = file;
    if (!file) {
        detectionResult.value = null;
    }
};

function handleRunAnalysis() {
    if (!selectedFile.value) return alert("Please select a file first.");

    loading.value = true;
    detectionResult.value = null;
    form.image = selectedFile.value;

    form.post(route("scans.store"), {
        forceFormData: true,
        preserveScroll: true,
        onSuccess: () => {
            successToast("Analysis completed successfully!");
        },
        onError: (errors) => {
            console.error("Analysis failed:", errors);
            errorToast("Analysis failed. Please try again.");
        },
        // The loading state should be turned off when the request finishes.
        onFinish: () => {
            loading.value = false;
        },
    });
}

// --- Batch Image Analysis ---
const isProcessing = ref(false);
const isSuccess = ref(false);
const processedCount = ref(0);
const totalCount = ref(0);
const batchRef = ref(null);

async function handleRunBatchAnalysis(files) {
    isProcessing.value = true;
    isSuccess.value = false;
    processedCount.value = 0;
    totalCount.value = files.length;

    const formData = new FormData();
    files.forEach((fileWrapper) => {
        formData.append("images[]", fileWrapper.file);
    });

    try {
        const response = await axios.post(route("scans.store.batch"), formData);
        const batchId = response.data.batch_id;

        const intervalId = setInterval(async () => {
            try {
                const statusResponse = await axios.get(
                    route("scans.batch.status", { batchId })
                );
                const { processed, total } = statusResponse.data;
                processedCount.value = processed;
                totalCount.value = total;

                if (total > 0 && processed >= total) {
                    clearInterval(intervalId);
                    isProcessing.value = false;
                    isSuccess.value = true;
                }
            } catch (error) {
                console.error("Failed to get batch status:", error);
                clearInterval(intervalId);
                isProcessing.value = false;
            }
        }, 1000);
    } catch (error) {
        console.error("Failed to start batch:", error);
        isProcessing.value = false;
    }
}

function resetBatch() {
    isSuccess.value = false;
    processedCount.value = 0;
    totalCount.value = 0;
    batchRef.value?.clearFiles();
}

// --- Watchers ---
watch(
    () => props.scanResult,
    (newResults) => {
        if (newResults) {
            detectionResult.value = newResults;
        }
    }
);
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
