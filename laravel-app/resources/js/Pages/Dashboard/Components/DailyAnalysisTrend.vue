<script setup>
import VueApexCharts from "vue3-apexcharts";
import { ref, computed } from "vue";

const props = defineProps({
    dailyData: {
        type: Object,
        required: true,
    },
});

const series = computed(() => [
    {
        name: "Defect Count",
        data: props.dailyData.totalDefective || [],
    },
    {
        name: "Total Processed",
        data: props.dailyData.totalProcessed || [],
    },
]);

const chartOptions = computed(() => ({
    chart: {
        toolbar: {
            show: false,
        },
    },
    plotOptions: {
        bar: {
            horizontal: false,
            columnWidth: "55%",
            borderRadius: 5,
        },
    },
    dataLabels: {
        enabled: false,
    },
    stroke: {
        show: true,
        width: 2,
        colors: ["transparent"],
    },
    fill: {
        opacity: 1,
    },
    tooltip: {
        y: {
            formatter: (val) => `${val} items`,
        },
    },
    legend: {
        position: "top",
        horizontalAlign: "right",
        fontSize: "14px",
        markers: {
            radius: 12,
        },
        labels: {
            colors: "#cbd5e1",
        },
    },
    colors: ["#dc2626", "#059669"], // red for defects, green for processed
    xaxis: {
        categories: props.dailyData.labels || [],
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
}));
</script>

<template>
    <div class="mx-auto w-full max-w-4xl">
        <VueApexCharts
            type="bar"
            height="500"
            :options="chartOptions"
            :series="series"
        />
    </div>
</template>
