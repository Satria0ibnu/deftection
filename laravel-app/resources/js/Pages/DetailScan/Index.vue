<script setup>
import { ref, computed } from "vue";
import { useForm } from "@inertiajs/vue3";
import { route } from "ziggy-js";
import {
    successToast,
    errorToast,
    deleteConfirmDialog,
    exportConfirmDialog,
} from "@/utils/swal";

import AnalysisSummary from "./Components/AnalysisSummary.vue";
import ImageComparison from "./Components/ImageComparison.vue";
import DefectDetailCharts from "./Components/DefectDetailCharts.vue";
import PerformanceChart from "./Components/PerformanceChart.vue";
import ProductQuality from "./Components/ProductQuality.vue";
import TechnicalDetails from "./Components/TechnicalDetails.vue";

// --- Props Definition ---
const props = defineProps({
    analysis: {
        type: Object,
        required: true,
    },
    title: {
        type: String,
        default: "Scan Analysis Details",
    },
    scan: {
        type: Object,
        default: () => ({}),
    },
});

// Loading states
const isDeleting = ref(false);
const isExporting = ref(false);

// Check if any operation is in progress
const isOperationInProgress = computed(() => {
    return isDeleting.value || isExporting.value;
});

// --- Computed Properties ---
const isDefectStatus = computed(() => props.analysis?.status === "defect");
const isGoodStatus = computed(() => props.analysis?.status === "good");
const hasValidAnalysis = computed(
    () => props.analysis && props.analysis.summary
);

// Handle download with confirmation
const handleDownload = async () => {
    try {
        // Show export confirmation dialog
        const result = await exportConfirmDialog({
            title: "Export analysis report?",
            text: `This will generate and download a PDF report for analysis "${props.analysis.summary?.imageName}" (ID: ${props.analysis.id}). Are you sure you want to proceed?`,
        });

        if (result.isConfirmed) {
            await performExport();
        }
    } catch (error) {
        console.error("Export confirmation failed:", error);
        errorToast("Failed to show export confirmation dialog");
    }
};

// Perform the actual export
const performExport = async () => {
    try {
        isExporting.value = true;

        // Create a form for the export request
        const form = document.createElement("form");
        form.method = "GET";
        form.action = route("reports.single.generate", props.analysis.id);
        form.target = "_blank"; // Open in new tab

        // Add CSRF token if available
        const csrfToken = document
            .querySelector('meta[name="csrf-token"]')
            ?.getAttribute("content");
        if (csrfToken) {
            const csrfInput = document.createElement("input");
            csrfInput.type = "hidden";
            csrfInput.name = "_token";
            csrfInput.value = csrfToken;
            form.appendChild(csrfInput);
        }

        // Append form to body, submit, then remove
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);

        // Show success message
        successToast(
            "Report generation started! The download will begin shortly.",
            5000
        );

        console.log("Export initiated for analysis ID:", props.analysis.id);
    } catch (error) {
        console.error("Export request failed:", error);
        errorToast("Failed to initiate report generation.");
    } finally {
        isExporting.value = false;
    }
};

// Handle delete with confirmation
const handleDelete = async () => {
    try {
        // Show confirmation dialog with analysis details
        const analysisDescription = `"${props.analysis.summary?.imageName}" (Analysis ID: ${props.analysis.id})`;
        const result = await deleteConfirmDialog(analysisDescription);

        if (result.isConfirmed) {
            await performDelete();
        }
    } catch (error) {
        console.error("Delete confirmation failed:", error);
        errorToast("Failed to show delete confirmation dialog");
    }
};

// Perform the actual deletion
const performDelete = async () => {
    try {
        isDeleting.value = true;

        const form = useForm({});

        form.delete(route("scans.destroy", props.analysis.id), {
            preserveState: true,
            preserveScroll: true,
            onSuccess: () => {
                handleDeleteSuccess();
            },
            onError: (errors) => {
                handleDeleteError(errors);
            },
            onFinish: () => {
                isDeleting.value = false;
            },
        });
    } catch (error) {
        console.error("Delete operation failed:", error);
        errorToast("An unexpected error occurred while deleting the analysis.");
        isDeleting.value = false;
    }
};

// Handle successful deletion
const handleDeleteSuccess = () => {
    console.log("Analysis deleted successfully:", props.analysis.id);

    successToast("Analysis deleted successfully!");

    // Navigate to scan history or reload page
    window.location.href = route("scans.index");
};

// Handle deletion error
const handleDeleteError = (errors) => {
    console.error("Delete operation failed:", errors);

    let errorMessage =
        "An unexpected error occurred while deleting the analysis.";

    // Check for specific error messages
    if (errors.message) {
        errorMessage = errors.message;
    } else if (errors.error) {
        errorMessage = errors.error;
    }

    errorToast(errorMessage);
};
</script>

<template>
    <!-- Error State -->
    <div
        v-if="!hasValidAnalysis"
        class="bg-red-50 p-6 border border-red-200 rounded-lg"
    >
        <div class="flex items-center">
            <div class="flex-shrink-0">
                <svg
                    class="w-5 h-5 text-red-400"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                >
                    <path
                        fill-rule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clip-rule="evenodd"
                    />
                </svg>
            </div>
            <div class="ml-3">
                <h3 class="font-medium text-red-800 text-sm">
                    Analysis Data Missing
                </h3>
                <div class="mt-2 text-red-700 text-sm">
                    <p>
                        Unable to load scan analysis data. Please try refreshing
                        the page or contact support.
                    </p>
                </div>
            </div>
        </div>
    </div>

    <!-- Main Content -->
    <div v-else class="flex flex-col gap-6">
        <!-- Page Title -->
        <div class="flex justify-between pb-4 border-gray-200 border-b">
            <div class="flex flex-col gap-1">
                <h1 class="font-bold text-gray-900 dark:text-dark-50 text-2xl">
                    {{ title }}
                </h1>
                <p class="mt-1 text-sm">
                    Analysis for {{ props.analysis.summary?.imageName }} • Scan
                    ID: {{ props.analysis.id }} •
                    {{ props.analysis.summary?.analysisDate }}
                </p>
            </div>
            <div class="flex items-end gap-3">
                <button
                    @click="handleDownload"
                    :disabled="isOperationInProgress"
                    class="gap-2 bg-this hover:bg-this-darker focus:bg-this-darker active:bg-this-darker/90 disabled:bg-this-light dark:disabled:bg-this-darker text-white btn-base btn this:primary"
                    :class="{
                        'opacity-50 cursor-not-allowed': isOperationInProgress,
                    }"
                >
                    <div v-if="isExporting" class="flex items-center">
                        <svg
                            class="mr-2 w-4 h-4 animate-spin"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                        >
                            <circle
                                class="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                stroke-width="4"
                            ></circle>
                            <path
                                class="opacity-75"
                                fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            ></path>
                        </svg>
                        <span>Exporting...</span>
                    </div>
                    <div v-else class="flex items-center">
                        <font-awesome-icon icon="fa-solid fa-download" />
                        <span>Download</span>
                    </div>
                </button>
                <button
                    @click="handleDelete"
                    :disabled="isOperationInProgress"
                    class="gap-2 bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 text-white transition-colors btn-base btn"
                    :class="{
                        'opacity-50 cursor-not-allowed': isOperationInProgress,
                    }"
                >
                    <div v-if="isDeleting" class="flex items-center">
                        <svg
                            class="mr-2 w-4 h-4 animate-spin"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                        >
                            <circle
                                class="opacity-25"
                                cx="12"
                                cy="12"
                                r="10"
                                stroke="currentColor"
                                stroke-width="4"
                            ></circle>
                            <path
                                class="opacity-75"
                                fill="currentColor"
                                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            ></path>
                        </svg>
                        <span>Deleting...</span>
                    </div>
                    <div v-else class="flex items-center">
                        <font-awesome-icon icon="fa-solid fa-trash-can" />
                        <span>Delete</span>
                    </div>
                </button>
            </div>
        </div>

        <!-- Analysis Summary (Updated with new structure) -->
        <AnalysisSummary :summary="props.analysis.summary" />

        <!-- Image Comparison -->
        <ImageComparison :comparison-data="props.analysis.visuals" />

        <!-- Defect Details (only for defect status) -->
        <DefectDetailCharts
            v-if="isDefectStatus"
            :defects="props.analysis.defects"
        />

        <!-- Performance Chart (Updated - now shows processing performance) -->
        <PerformanceChart :performance-data="props.analysis.performance" />

        <!-- Product Quality (only for good status) -->
        <ProductQuality v-if="isGoodStatus" />

        <!-- Technical Details (Updated with new structure) -->
        <TechnicalDetails :details="props.analysis.technical" />
    </div>
</template>
