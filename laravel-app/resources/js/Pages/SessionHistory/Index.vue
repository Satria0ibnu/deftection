<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { router } from "@inertiajs/vue3";
import { useDebounceFn } from "@vueuse/core";
import { route } from "ziggy-js";
import { useForm } from "@inertiajs/vue3";
import { successToast, errorToast, deleteConfirmDialog } from "@/utils/swal";
import { usePolling } from "@/composables/usePolling";

// Import shared components
import Table from "../../Shared/Table/Table.vue";
import Tablewrapper from "../../Shared/Table/Tablewrapper.vue";
import TableToolbar from "../../Shared/Table/TableToolbar.vue";
import TableContainer from "../../Shared/Table/TableContainer.vue";
import ToolbarSearch from "../../Shared/TableToolbar/ToolbarSearch.vue";
import TableHeaderCell from "../../Shared/Table/TableHeaderCell.vue";
import ForceRefreshButton from "../../Shared/Table/ForceRefreshButton.vue";
import LiveMonitorToggle from "../../Shared/Table/LiveMonitorToggle.vue";
import TableCell from "../../Shared/Table/TableCell.vue";
import RowNotFound from "../../Shared/Table/RowNotFound.vue";
import TableFooter from "../../Shared/Table/TableFooter.vue";
import EllipsisDropdown from "../../Shared/Dropdown/EllipsisDropdown.vue";
import DetailViewList from "../../Shared/Dropdown/ViewItem.vue";
import DeleteItem from "../../Shared/Dropdown/DeleteItem.vue";

// --- Props ---
// This page receives its data from the RealtimeController@index method.
const props = defineProps({
    sessions: { type: Object, required: true },
    filters: { type: Object, required: true },
    meta: { type: Object, default: () => ({}) },
    initialChecksum: { type: String, default: "" },
});

// --- State ---
const currentFilters = computed(() => props.filters?.current || {});
const searchTerm = ref(currentFilters.value.search || "");
const isTableLoading = ref(false);

// --- Polling State ---
const pollingSessions = ref([]);
const pollingMeta = ref({});
const displaySessions = computed(() => {
    return pollingSessions.value.length > 0
        ? pollingSessions.value.data
        : props.sessions?.data || [];
});

// FIX: Provide a safe fallback object to prevent errors when props are not available.
const displayMeta = computed(() => {
    if (Object.keys(pollingMeta.value).length > 0) {
        return pollingMeta.value;
    }
    if (props.sessions) {
        return props.sessions;
    }
    // Fallback for mock data mode
    return {
        total: 0,
        from: 0,
        to: 0,
        links: [],
    };
});

// --- Polling Logic ---
const {
    isPolling,
    isLoading: isPollingLoading,
    isManuallyPaused,
    isOnline,
    visibility,
    togglePolling,
    forceRefresh,
    initializeChecksum,
} = usePolling({
    checkUrl: route("sessions.index.check"),
    dataUrl: route("sessions.index.api"),
    forceRefreshUrl: route("sessions.index.refresh"),
    interval: 20000,
    enabled: true,
    onDataUpdate: (data) => {
        pollingSessions.value = data.sessions || [];
        pollingMeta.value = data.sessions || {};
    },
    onError: (error) => {
        console.error("Session polling error:", error);
    },
});

onMounted(() => {
    initializeChecksum(props.initialChecksum);
});

// --- Helper Functions ---
const getStatusClass = (status) => {
    if (status === "Completed") return "text-green-500";
    if (status === "Interrupted") return "text-yellow-500";
    return "text-gray-500";
};

// --- Navigation & Actions ---
const navigateWithFilters = (customParams = {}) => {
    isTableLoading.value = true;
    const params = {
        search: searchTerm.value || undefined,
        page: 1,
        ...customParams,
    };
    router.get(route("sessions.index"), params, {
        preserveState: true,
        preserveScroll: true,
        replace: true,
        only: ["sessions", "filters", "meta", "initialChecksum"],
        onSuccess: (page) => initializeChecksum(page.props.initialChecksum),
        onFinish: () => {
            isTableLoading.value = false;
        },
    });
};

const debouncedSearch = useDebounceFn(() => navigateWithFilters(), 300);
watch(searchTerm, debouncedSearch);

const goToPage = (page) => navigateWithFilters({ page });
const changePerPage = (perPage) =>
    navigateWithFilters({ per_page: perPage, page: 1 });

const handleDeleteSession = async (session) => {
    const result = await deleteConfirmDialog(`session "${session.id}"`);
    if (result.isConfirmed) {
        router.delete(route("sessions.destroy", session.id), {
            preserveScroll: true,
            onSuccess: () => successToast("Session deleted successfully!"),
            onError: () => errorToast("Failed to delete session."),
        });
    }
};
</script>

<template>
    <Tablewrapper>
        <div class="flex justify-between items-center mb-4">
            <LiveMonitorToggle
                :isPolling="isPolling"
                :isPollingLoading="isPollingLoading"
                :isManuallyPaused="isManuallyPaused"
                :isOnline="isOnline"
                :visibility="visibility"
                @click="togglePolling"
            />
            <ForceRefreshButton
                :isPollingLoading="isPollingLoading"
                :isOnline="isOnline"
                :disabled="isTableLoading"
                @click="forceRefresh"
            />
        </div>

        <TableToolbar
            title="Session History"
            description="History of your real-time detection sessions"
        >
            <template #left>
                <ToolbarSearch
                    v-model="searchTerm"
                    placeholder="Search by Session ID..."
                />
            </template>
        </TableToolbar>

        <TableContainer>
            <Table>
                <template #head>
                    <tr class="group/tr table-tr">
                        <TableHeaderCell label="Session ID" />
                        <TableHeaderCell label="Date" />
                        <TableHeaderCell label="Duration" />
                        <TableHeaderCell label="Total Scans" />
                        <TableHeaderCell label="Defect Rate" />
                        <TableHeaderCell label="Status" />
                        <TableHeaderCell label="Actions" :is-sortable="false" />
                    </tr>
                </template>
                <template #body>
                    <tr
                        v-for="session in displaySessions"
                        :key="session.id"
                        class="group/tr table-tr border-y border-transparent border-b-gray-200 dark:border-b-dark-500"
                    >
                        <TableCell>
                            <p
                                class="font-medium text-gray-800 dark:text-dark-100"
                            >
                                {{ session.id }}
                            </p>
                        </TableCell>
                        <TableCell>
                            <p class="text-gray-800 dark:text-dark-100">
                                {{ session.date }}
                            </p>
                        </TableCell>
                        <TableCell>
                            <p class="text-gray-800 dark:text-dark-100">
                                {{ session.duration }}
                            </p>
                        </TableCell>
                        <TableCell>
                            <p
                                class="font-mono text-gray-800 dark:text-dark-100"
                            >
                                {{ session.total_scans }}
                            </p>
                        </TableCell>
                        <TableCell>
                            <p
                                class="font-mono font-semibold"
                                :class="
                                    session.defect_rate > 10
                                        ? 'text-red-500'
                                        : 'text-gray-800 dark:text-dark-100'
                                "
                            >
                                {{ session.defect_rate.toFixed(1) }}%
                            </p>
                        </TableCell>
                        <TableCell>
                            <p
                                class="font-semibold"
                                :class="getStatusClass(session.status)"
                            >
                                {{ session.status }}
                            </p>
                        </TableCell>
                        <TableCell>
                            <EllipsisDropdown>
                                <!-- This now correctly links to the list of scans for this session -->
                                <DetailViewList
                                    label="View Scans"
                                    :href="
                                        route('sessions_scan.index', {
                                            session: session.id,
                                        })
                                    "
                                />
                                <DeleteItem
                                    label="Delete Session"
                                    @click="handleDeleteSession(session)"
                                />
                            </EllipsisDropdown>
                        </TableCell>
                    </tr>
                    <RowNotFound
                        v-if="displaySessions.length === 0"
                        label="No sessions found"
                    />
                </template>
            </Table>

            <TableFooter
                :meta="displayMeta"
                :currentFilters="currentFilters"
                @goToPage="goToPage"
                @changePerPage="changePerPage"
            />
        </TableContainer>
    </Tablewrapper>
</template>
