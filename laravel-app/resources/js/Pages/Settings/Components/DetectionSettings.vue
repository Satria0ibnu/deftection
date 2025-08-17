<script setup>
import { computed } from "vue";

// --- Props ---
// This component receives the current detection settings from the parent page.
const props = defineProps({
    settings: {
        type: Object,
        required: true,
    },
});

// --- Emits ---
// Defines the event that will be sent to the parent component.
const emit = defineEmits(["update:settings"]);

// --- Local Computed Form ---
// This computed property acts as a two-way binding. It reads from the prop
// but emits an event when a change is made, rather than modifying the prop directly.
const form = computed({
    get() {
        return props.settings;
    },
    set(newSettings) {
        emit("update:settings", newSettings);
    },
});
</script>

<template>
    <div
        class="px-6 py-5 bg-white border border-gray-200 rounded-lg shadow-sm dark:bg-dark-800 dark:shadow-none dark:border-none"
    >
        <!-- Section 1: Detection Configuration -->
        <div class="flex flex-col">
            <h2
                class="mb-1 flex items-center text-lg font-semibold text-gray-900 dark:text-dark-50"
            >
                Detection Configuration
            </h2>
            <p class="mb-6 text-xs text-gray-400 dark:text-dark-300">
                Configure AI detection parameters and thresholds.
            </p>

            <div class="grid grid-cols-1 gap-8 sm:grid-cols-2">
                <!-- Anomaly Detection Threshold Slider -->
                <div>
                    <label
                        for="anomalyThreshold"
                        class="mb-1 text-sm font-medium text-gray-800 dark:text-dark-100"
                        >Anomaly Detection Threshold</label
                    >
                    <div class="flex items-center my-2 space-x-4">
                        <span class="text-xs">0.1</span>
                        <input
                            v-model.number="form.anomalyThreshold"
                            type="range"
                            id="anomalyThreshold"
                            min="0.1"
                            max="1.0"
                            step="0.05"
                            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-dark-700"
                        />
                        <span class="text-xs">1.0</span>
                    </div>
                    <div class="flex justify-between">
                        <p class="text-xs">Sensitive</p>
                        <p
                            class="text-xs font-bold text-blue-600 dark:text-blue-400"
                        >
                            {{ form.anomalyThreshold.toFixed(2) }}
                        </p>
                        <p class="text-xs">Conservative</p>
                    </div>
                </div>
                <!-- Defect Classification Threshold Slider -->
                <div>
                    <label
                        for="defectThreshold"
                        class="mb-1 text-sm font-medium text-gray-800 dark:text-dark-100"
                        >Defect Classification Threshold</label
                    >
                    <div class="flex items-center my-2 space-x-4">
                        <span class="text-xs">0.1</span>
                        <input
                            v-model.number="form.defectThreshold"
                            type="range"
                            id="defectThreshold"
                            min="0.1"
                            max="1.0"
                            step="0.05"
                            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-dark-700"
                        />
                        <span class="text-xs">1.0</span>
                    </div>
                    <div class="flex justify-between">
                        <p class="text-xs">Sensitive</p>
                        <p
                            class="text-xs font-bold text-blue-600 dark:text-blue-400"
                        >
                            {{ form.defectThreshold.toFixed(2) }}
                        </p>
                        <p class="text-xs">Conservative</p>
                    </div>
                </div>
            </div>
        </div>

        <hr class="my-6 border-gray-200 dark:border-dark-600" />

        <!-- Section 2: Export Settings -->
        <div>
            <h2
                class="flex items-center text-lg font-semibold text-gray-900 dark:text-dark-50"
            >
                Export Settings
            </h2>
            <div class="mt-6">
                <label
                    for="exportFormat"
                    class="text-sm font-medium text-gray-800 dark:text-dark-100"
                    >Preferred Export Format</label
                >
                <div class="mt-1 max-w-xs">
                    <div class="input-root undefined">
                        <div class="input-wrapper relative">
                            <select
                                v-model="form.exportFormat"
                                id="exportFormat"
                                class="form-select-base form-select block w-full max-w-xs mt-1 text-sm ltr:pr-9 rtl:pl-9 peer border-gray-300 hover:border-gray-400 focus:border-primary-600 dark:border-dark-450 dark:hover:border-dark-400 dark:focus:border-primary-500"
                                disabled
                            >
                                <option value="pdf">PDF Report</option>
                            </select>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.dark #exportFormat {
    --bg-color: rgb(21, 22, 26);
}

#exportFormat {
    --bg-color: rgb(255, 255, 255);
}
</style>
