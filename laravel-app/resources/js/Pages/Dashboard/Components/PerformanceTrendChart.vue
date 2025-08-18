<script setup>
import VueApexCharts from "vue3-apexcharts";
import { computed } from "vue";

const props = defineProps({
    performanceData: {
        type: Object,
        required: true,
    },
});

const series = computed(() => [
    {
        name: "Defects Detected",
        data: props.performanceData.data || [],
    },
]);

const chartOptions = computed(() => ({
    colors: ["#a855f7"],
    chart: {
        dropShadow: {
            enabled: true,
            color: "#1E202C",
            top: 18,
            left: 6,
            blur: 8,
            opacity: 0.1,
        },
        toolbar: {
            show: false,
        },
    },
    stroke: {
        width: 8,
        curve: "smooth",
    },
    xaxis: {
        type: "category",
        categories: props.performanceData.labels || [],
        tickAmount: 10,
        labels: {
            style: {
                colors: "#cbd5e1",
            },
        },
    },
    yaxis: {
        labels: {
            style: {
                colors: "#cbd5e1",
            },
        },
    },
    fill: {
        type: "gradient",
        gradient: {
            shade: "dark",
            gradientToColors: ["#86efac"],
            shadeIntensity: 1,
            type: "horizontal",
            opacityFrom: 1,
            opacityTo: 0.95,
            stops: [0, 100, 0, 100],
        },
    },
    tooltip: {
        y: {
            formatter: (val) => `${val} defects`,
        },
    },
}));
</script>

<template>
    <div class="mx-auto w-full">
        <VueApexCharts
            type="line"
            height="350"
            :options="chartOptions"
            :series="series"
        />
    </div>
</template>
