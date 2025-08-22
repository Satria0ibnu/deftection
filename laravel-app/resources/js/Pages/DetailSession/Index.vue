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

// Import Shared Components
import Tablewrapper from "../../Shared/Table/Tablewrapper.vue";
import TableContainer from "../../Shared/Table/TableContainer.vue";
import Table from "../../Shared/Table/Table.vue";
import TableCell from "../../Shared/Table/TableCell.vue";
import TableHeaderCell from "../../Shared/Table/TableHeaderCell.vue";
import RowNotFound from "../../Shared/Table/RowNotFound.vue";
import ImageModal from "../../Shared/Modals/ImageModal.vue";

// Import Page-Specific Components
import Header from "./Components/Header.vue";
import Summary from "./Components/Summary.vue";
import DonutChart from "./Components/DonutChart.vue";
import PieChart from "./Components/PieChart.vue";

// --- Props ---
const props = defineProps({
    session: { type: Object, required: true },
});

// Loading states
const isDeleting = ref(false);
const isExporting = ref(false);

// State for image modal
const zoomedImageUrl = ref(null);

const openImageModal = (imageUrl) => {
    zoomedImageUrl.value = imageUrl;
};

const closeImageModal = () => {
    zoomedImageUrl.value = null;
};

// Check if any operation is in progress
const isOperationInProgress = computed(() => {
    return isDeleting.value || isExporting.value;
});

// --- Data Processing ---
const session = computed(() => props.session);

// --- Helper Functions ---
const getStatusClass = (status) => {
    if (status === "good")
        return "bg-green-100 text-green-800 dark:bg-green-500/10 dark:text-green-400";
    return "bg-red-100 text-red-800 dark:bg-red-500/10 dark:text-red-400";
};

const formatDecimal = (value) => Number(value).toFixed(3);

// Handle download with confirmation
const handleDownload = async () => {
    try {
        // Show export confirmation dialog
        const result = await exportConfirmDialog({
            title: "Export session report?",
            text: `This will generate and download a PDF report for session "${session.value.id}". Are you sure you want to proceed?`,
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
        form.action = route("reports.session.generate", session.value.id);
        form.target = "_blank";

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
            "Session report generation started! The download will begin shortly.",
            10000
        );

        console.log("Export initiated for session ID:", session.value.id);
    } catch (error) {
        console.error("Export request failed:", error);
        errorToast("Failed to initiate session report generation.");
    } finally {
        isExporting.value = false;
    }
};

// Handle delete with confirmation
const handleDelete = async () => {
    try {
        // Show confirmation dialog with session details
        const result = await deleteConfirmDialog(
            'session "' + session.value.id + '"'
        );

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

        form.delete(route("sessions.destroy", session.value.id), {
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
        errorToast("An unexpected error occurred while deleting the session.");
        isDeleting.value = false;
    }
};

// Handle successful deletion
const handleDeleteSuccess = () => {
    console.log("Session deleted successfully:", session.value.id);

    successToast("Session deleted successfully!");

    // Navigate to session history or reload page
    window.location.href = route("sessions.index");
};

// Handle deletion error
const handleDeleteError = (errors) => {
    console.error("Delete operation failed:", errors);

    let errorMessage =
        "An unexpected error occurred while deleting the session.";

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
    <div class="flex flex-col gap-6">
        <!-- Session Header -->
        <Header
            :session="session"
            @download="handleDownload"
            @delete="handleDelete"
        />

        <!-- Key Metrics Summary -->
        <Summary :session="session" />

        <!-- Charts -->
        <div class="gap-6 grid grid-cols-1 sm:grid-cols-2">
            <DonutChart :session="session" />
            <PieChart :session="session" />
        </div>

        <!-- Scans Table -->
        <Tablewrapper>
            <TableContainer>
                <Table>
                    <template #head>
                        <tr class="group/tr table-tr">
                            <TableHeaderCell label="Image" />
                            <TableHeaderCell label="Timestamp" />
                            <TableHeaderCell label="Status" />
                            <TableHeaderCell label="Score" />
                        </tr>
                    </template>
                    <template #body>
                        <tr
                            v-for="scan in session.scans"
                            :key="scan.id"
                            class="group/tr table-tr border-b-gray-200 dark:border-b-dark-500"
                        >
                            <TableCell>
                                <div class="flex items-center">
                                    <img
                                        class="flex-shrink-0 rounded-md w-16 h-10 object-cover cursor-pointer hover:opacity-80 transition-opacity duration-400 ease-in-out"
                                        :src="scan.annotated_path"
                                        alt="Scan Image"
                                        @click="
                                            openImageModal(scan.annotated_path)
                                        "
                                    />
                                    <p
                                        class="ml-4 font-medium text-gray-800 dark:text-dark-100"
                                    >
                                        {{ scan.filename }}
                                    </p>
                                </div>
                            </TableCell>
                            <TableCell>
                                <p class="text-gray-800 dark:text-dark-100">
                                    {{
                                        new Date(
                                            scan.created_at
                                        ).toLocaleTimeString()
                                    }}
                                </p>
                            </TableCell>
                            <TableCell>
                                <span
                                    :class="getStatusClass(scan.status)"
                                    class="inline-flex px-2 rounded-full font-semibold text-xs leading-5"
                                >
                                    {{ scan.status.toUpperCase() }}
                                </span>
                            </TableCell>
                            <TableCell>
                                <p
                                    class="font-mono text-gray-800 dark:text-dark-100"
                                >
                                    {{ formatDecimal(scan.anomaly_score) }}
                                </p>
                            </TableCell>
                        </tr>
                        <RowNotFound
                            v-if="!session.scans || session.scans.length === 0"
                            label="No scans found for this session"
                        />
                    </template>
                </Table>
            </TableContainer>
        </Tablewrapper>
    </div>

    <ImageModal :image-url="zoomedImageUrl" @close="closeImageModal" />
</template>
