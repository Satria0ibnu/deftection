<script setup>
import { computed } from "vue";
import VueApexCharts from "vue3-apexcharts";

// --- Props ---
const props = defineProps({
    session: {
        type: Object,
        required: true,
    },
});

// --- Chart Data Processing ---
// It expects a `defectDistribution` object like: { 'Scratch': 10, 'Dent': 5 }
const chartData = computed(() => {
    const distribution = props.session.defectDistribution || {};

    return {
        labels: Object.keys(distribution),
        data: Object.values(distribution),
    };
});

// --- Chart Configuration ---
const donutChartSeries = computed(() => chartData.value.data);

// The options for the donut chart, adapted from your original and reference components.
const donutChartOptions = computed(() => {
    const isDarkMode = localStorage.getItem("theme") === "dark";

    return {
        chart: {
            type: "donut",
            toolbar: { show: false },
        },
        labels: chartData.value.labels,
        dataLabels: {
            enabled: true, // Often useful to show values on the donut slices
        },
        legend: {
            position: "bottom",
            horizontalAlign: "center",
            labels: {
                colors: isDarkMode ? "#9CA3AF" : "#6B7280",
            },
        },
        tooltip: {
            theme: isDarkMode ? "dark" : "light",
            y: {
                // Formatter from your reference component
                formatter: (val) => `${val} defects`,
            },
        },
        // Using the monochrome theme from your reference for a clean look
        theme: {
            monochrome: {
                enabled: true,
                color: "#EF4444", // Using the blue from your original line chart
                shadeTo: "light",
                shadeIntensity: 0.65,
            },
        },
    };
});
</script>

<template>
    <div class="bg-white dark:bg-dark-800 shadow p-6 rounded-lg">
        <h2
            class="font-medium text-gray-800 dark:text-dark-100 text-sm-plus tracking-wide"
        >
            Defect Type Distribution
        </h2>
        <div class="mt-4 h-auto">
            <!-- Display a message if there is no data to show -->
            <div
                v-if="!donutChartSeries.length"
                class="flex justify-center items-center h-64 text-gray-500 dark:text-dark-300"
            >
                No defect data available.
            </div>
            <!-- Render the chart only if there is data -->
            <VueApexCharts
                v-else
                type="donut"
                height="450"
                :options="donutChartOptions"
                :series="donutChartSeries"
            />
        </div>
    </div>
</template>
