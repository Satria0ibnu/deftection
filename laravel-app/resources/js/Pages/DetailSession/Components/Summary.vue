<script setup>
// --- Props ---
// This component receives the main session object to display its summary data.
const props = defineProps({
    session: {
        type: Object,
        required: true,
    },
});
</script>

<template>
    <!-- Section 2: Key Metrics Summary -->
    <div class="gap-4 grid grid-cols-2 sm:grid-cols-4">
        <div class="space-y-1 bg-white dark:bg-dark-800 shadow p-4 rounded-lg">
            <p class="text-xs-plus uppercase">Duration</p>
            <p class="font-semibold text-gray-800 dark:text-dark-100 text-2xl">
                {{ session.duration }}
            </p>
        </div>
        <div class="space-y-1 bg-white dark:bg-dark-800 shadow p-4 rounded-lg">
            <p class="text-xs-plus uppercase">Total Scans</p>
            <p class="font-bold text-gray-800 dark:text-dark-100 text-2xl">
                {{ session.total_scans }}
            </p>
        </div>
        <div class="space-y-1 bg-white dark:bg-dark-800 shadow p-4 rounded-lg">
            <p class="text-xs-plus uppercase">Good / Defect</p>
            <p class="font-bold text-2xl">
                <span class="text-green-500">{{ session.good_scans }}</span>
                /
                <span class="text-red-500">{{ session.defected_scans }}</span>
            </p>
        </div>
        <div class="space-y-1 bg-white dark:bg-dark-800 shadow p-4 rounded-lg">
            <p class="text-xs-plus uppercase">Defect Rate</p>
            <p class="font-bold text-red-500 text-2xl">
                {{ Number(session.defect_rate).toFixed(1) }}%
            </p>
        </div>
    </div>
</template>
