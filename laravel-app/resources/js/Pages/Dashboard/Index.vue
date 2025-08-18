<script setup>
import StatsCard from "./Components/StatsCard.vue";
import PerformanceTrendChart from "./Components/PerformanceTrendChart.vue";
import DefectTypeChart from "./Components/DefectTypeChart.vue";
import DailyAnalysisTrend from "./Components/DailyAnalysisTrend.vue";
import RecentAnalysisTable from "./Components/RecentAnalysisTable.vue";
import AnalysisOverview from "./Components/AnalysisOverview.vue";

// Props from DashboardService
const props = defineProps({
    cardData: {
        type: Object,
        required: true,
    },
    dailyAnalysis: {
        type: Object,
        required: true,
    },
    defectType: {
        type: Object,
        required: true,
    },
    performanceTrend: {
        type: Object,
        required: true,
    },
    recentAnalyses: {
        type: Array,
        required: true,
    },
    analysesOverview: {
        type: Object,
        required: true,
    },
});
</script>

<template>
    <!-- Status Grid -->
    <div class="gap-6 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 pb-6">
        <!-- Total Defects -->
        <StatsCard
            title="Total Defects"
            :value="cardData.totalDefective"
            description="Total number of defects detected."
            badgeColor="primary"
            :changeRate="cardData.defectiveChangeRate"
        >
            <template #icon>
                <font-awesome-icon icon="fa-solid fa-bug" />
            </template>
        </StatsCard>

        <!-- Images Processed -->
        <StatsCard
            title="Images Processed"
            :value="cardData.totalScansImage"
            description="Number of images processed."
            badgeColor="success"
            :changeRate="cardData.scansChangeRate"
        >
            <template #icon>
                <font-awesome-icon icon="fa-solid fa-images" />
            </template>
        </StatsCard>

        <!-- Realtime Sessions -->
        <StatsCard
            title="Realtime Sessions"
            :value="cardData.totalRealtimeSessions"
            description="Number of realtime sessions."
            badgeColor="secondary"
            :changeRate="cardData.sessionsChangeRate"
        >
            <template #icon>
                <font-awesome-icon icon="fa-solid fa-video" />
            </template>
        </StatsCard>

        <!-- Frames Processed -->
        <StatsCard
            title="Frames Processed"
            :value="cardData.totalFramesProcessed"
            description="Total frames from realtime sessions."
            badgeColor="error"
            :changeRate="cardData.framesChangeRate"
        >
            <template #icon>
                <font-awesome-icon icon="fa-solid fa-film" />
            </template>
        </StatsCard>
    </div>

    <!-- Daily Analysis Trend & Defect Type Distribution -->
    <div class="gap-6 grid grid-cols-1 md:grid-cols-2 py-6">
        <div
            class="flex flex-col justify-start items-start p-6 border border-gray-200 dark:border-dark-700 rounded-lg"
        >
            <h2
                class="font-medium text-gray-800 dark:text-dark-100 text-sm-plus tracking-wide"
            >
                Daily Analysis Trend (7 Days)
            </h2>

            <DailyAnalysisTrend :dailyData="dailyAnalysis" />
        </div>
        <div
            class="flex flex-col justify-start p-6 border border-gray-200 dark:border-dark-700 rounded-lg"
        >
            <h2
                class="font-medium text-gray-800 dark:text-dark-100 text-sm-plus tracking-wide"
            >
                Defect Type Distribution
            </h2>

            <DefectTypeChart :defectData="defectType" />
        </div>
    </div>

    <!-- Performance Trend -->
    <div class="grid grid-cols-1 py-6">
        <div
            class="flex flex-col justify-start p-6 border border-gray-200 dark:border-dark-700 rounded-lg"
        >
            <h2
                class="font-medium text-gray-800 dark:text-dark-100 text-sm-plus tracking-wide"
            >
                Performance Trend (30 Days)
            </h2>

            <PerformanceTrendChart :performanceData="performanceTrend" />
        </div>
    </div>

    <!-- Recent Analysis Table & Analysis Widget -->
    <div class="gap-6 grid grid-cols-1 md:grid-cols-2 py-6">
        <div
            class="flex flex-col justify-start gap-4 p-6 border border-gray-200 dark:border-dark-700 rounded-lg"
        >
            <div class="flex justify-between items-center">
                <h2
                    class="font-medium text-gray-800 dark:text-dark-100 text-sm-plus tracking-wide"
                >
                    Recent Analysis
                </h2>
                <a
                    :href="route('scans.index')"
                    class="pb-0.5 border-current border-b border-dotted outline-hidden font-medium text-primary-600 hover:text-primary-600/70 focus:text-primary-600/70 dark:hover:text-primary-400/70 dark:focus:text-primary-400/70 dark:text-primary-400 text-xs-plus transition-colors duration-300"
                >
                    <span>View all</span>
                </a>
            </div>

            <RecentAnalysisTable :analyses="recentAnalyses" />
        </div>
        <div
            class="flex flex-col justify-start gap-4 p-6 border border-gray-200 dark:border-dark-700 rounded-lg"
        >
            <h2
                class="font-medium text-gray-800 dark:text-dark-100 text-sm-plus tracking-wide"
            >
                Analysis Overview
            </h2>

            <AnalysisOverview :analyses="analysesOverview" />
        </div>
    </div>
</template>
