<script setup>
import VueApexCharts from "vue3-apexcharts";
import { computed } from "vue";

const props = defineProps({
    defectData: {
        type: Object,
        required: true,
    },
});

const series = computed(() => props.defectData.data || []);

const chartOptions = computed(() => ({
    labels: props.defectData.labels || [],
    fill: {
        opacity: 1,
    },
    stroke: {
        width: 1,
        colors: undefined,
    },
    yaxis: {
        show: false,
    },
    legend: {
        position: "bottom",
        horizontalAlign: "center",
        labels: {
            colors: "#cbd5e1",
        },
    },
    plotOptions: {
        polarArea: {
            rings: {
                strokeWidth: 0,
            },
            spokes: {
                strokeWidth: 0,
            },
        },
    },
    theme: {
        monochrome: {
            enabled: true,
            color: "#155dfc",
            shadeTo: "light",
            shadeIntensity: 0.65,
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
    <div class="mx-auto w-full max-w-4xl">
        <VueApexCharts
            type="pie"
            height="500"
            :options="chartOptions"
            :series="series"
        />
    </div>
</template>
