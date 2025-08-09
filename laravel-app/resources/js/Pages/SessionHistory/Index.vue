<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { router } from "@inertiajs/vue3";
import { useDebounceFn } from "@vueuse/core";
import { route } from "ziggy-js";
import { useForm } from "@inertiajs/vue3";
import { successToast, errorToast, deleteConfirmDialog } from "@/utils/swal";
import { Popover } from "@headlessui/vue";

// Import shared components
import Table from "../../Shared/Table/Table.vue";
import Tablewrapper from "../../Shared/Table/Tablewrapper.vue";
import TableToolbar from "../../Shared/Table/TableToolbar.vue";
import TableContainer from "../../Shared/Table/TableContainer.vue";
import ToolbarSearch from "../../Shared/TableToolbar/ToolbarSearch.vue";
import TableHeaderCell from "../../Shared/Table/TableHeaderCell.vue";
import FilterResetButton from "../../Shared/TableToolbar/FilterResetButton.vue";
import TableCell from "../../Shared/Table/TableCell.vue";
import RowNotFound from "../../Shared/Table/RowNotFound.vue";
import TableFooter from "../../Shared/Table/TableFooter.vue";
import EllipsisDropdown from "../../Shared/Dropdown/EllipsisDropdown.vue";
import DetailViewList from "../../Shared/Dropdown/ViewItem.vue";
import DeleteItem from "../../Shared/Dropdown/DeleteItem.vue";
import CreateButton from "../../Shared/TableToolbar/CreateButton.vue";

// --- Props ---
const props = defineProps({
    // sessions: { type: Object, required: true },
    // filters: { type: Object, required: true },
    // meta: { type: Object, default: () => ({}) },
});

// --- Mock Data ---
const mockSessions = ref([
    {
        id: "SESS-001",
        date: "2025-07-22",
        duration: "45 minutes",
        total_scans: 152,
        defect_rate: 5.2,
        status: "Completed",
    },
    {
        id: "SESS-002",
        date: "2025-07-21",
        duration: "1 hour 12 minutes",
        total_scans: 340,
        defect_rate: 7.8,
        status: "Completed",
    },
    {
        id: "SESS-003",
        date: "2025-07-21",
        duration: "22 minutes",
        total_scans: 88,
        defect_rate: 2.1,
        status: "Completed",
    },
    {
        id: "SESS-004",
        date: "2025-07-20",
        duration: "3 hours 5 minutes",
        total_scans: 890,
        defect_rate: 10.5,
        status: "Interrupted",
    },
    {
        id: "SESS-005",
        date: "2025-07-20",
        duration: "58 minutes",
        total_scans: 210,
        defect_rate: 4.0,
        status: "Completed",
    },
]);

// --- State ---
const searchTerm = ref("");
const displaySessions = ref(mockSessions.value);

// --- Helper Functions ---
const getStatusClass = (status) => {
    if (status === "Completed") return "text-green-500";
    if (status === "Interrupted") return "text-yellow-500";
    return "text-gray-500";
};

const handleViewDetails = (sessionId) => {
    console.log(`Navigating to scans for session: ${sessionId}`);
    // router.get(route('scans.history', { session_id: sessionId }));
};

const handleDeleteSession = (session) => {
    console.log(`Deleting session: ${session.id}`);
};

// --- Scroll Logic ---
const tableRef = ref(null);

const handleDropdownOpen = () => {
    setTimeout(() => {
        const wrapper = tableRef.value?.tableWrapperRef;
        if (wrapper) {
            if (wrapper.scrollHeight > wrapper.clientHeight) {
                wrapper.scrollTop = wrapper.scrollHeight;
            }
        }
    }, 60);
};
</script>

<template>
    <Tablewrapper>
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

            <template #right>
                <CreateButton
                    @click="() => router.get(route('sessions.create'))"
                    title="Create a new session"
                    label="New Session"
                />
            </template>
        </TableToolbar>

        <TableContainer>
            <Table ref="tableRef">
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
                        <!-- Session ID Column -->
                        <TableCell>
                            <p
                                class="font-medium text-gray-800 dark:text-dark-100"
                            >
                                {{ session.id }}
                            </p>
                        </TableCell>

                        <!-- Date Column -->
                        <TableCell>
                            <p class="text-gray-800 dark:text-dark-100">
                                {{ session.date }}
                            </p>
                        </TableCell>

                        <!-- Duration Column -->
                        <TableCell>
                            <p class="text-gray-800 dark:text-dark-100">
                                {{ session.duration }}
                            </p>
                        </TableCell>

                        <!-- Total Scans Column -->
                        <TableCell>
                            <p
                                class="font-mono text-gray-800 dark:text-dark-100"
                            >
                                {{ session.total_scans }}
                            </p>
                        </TableCell>

                        <!-- Defect Rate Column -->
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

                        <!-- Status Column -->
                        <TableCell>
                            <p
                                class="font-semibold"
                                :class="getStatusClass(session.status)"
                            >
                                {{ session.status }}
                            </p>
                        </TableCell>

                        <!-- Actions Column -->
                        <TableCell>
                            <EllipsisDropdown @click="handleDropdownOpen">
                                <DetailViewList
                                    label="View Scans"
                                    title="View all scans for this session"
                                    :href="route('scans.myscans')"
                                />
                                <DeleteItem
                                    label="Delete Session"
                                    title="Delete this session and all its scans"
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

            <!-- <TableFooter :meta="displayMeta" ... /> -->
        </TableContainer>
    </Tablewrapper>
</template>
