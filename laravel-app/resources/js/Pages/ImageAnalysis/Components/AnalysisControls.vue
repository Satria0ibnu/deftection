<script setup>
import { ref } from "vue";

defineProps({
    loading: Boolean,
});

// State
const sensitivity = ref(0.5);
const options = ref({
    threatChecker: false,
});

// Emits to parent (optional if you want to lift state up later)
const emit = defineEmits(["runAnalysis"]);
</script>

<template>
    <div class="pt-3">
        <!-- Sensitivity Slider -->
        <div class="mb-3">
            <label
                for="sensitivity"
                class="flex items-center gap-2 text-sm font-medium text-gray-800 dark:text-dark-100"
            >
                Sensitivity: <span class="font-bold">{{ sensitivity }}</span>
            </label>
            <input
                id="sensitivity"
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                v-model="sensitivity"
                class="my-2 form-range this:primary text-this dark:text-this-light"
            />

            <div
                class="mt-1 flex justify-between text-xs text-gray-800 dark:text-dark-100"
            >
                <span>0.1 (Low)</span>
                <span>1.0 (High)</span>
            </div>
        </div>

        <!-- Options -->
        <div class="space-y-2">
            <label class="flex items-center space-x-2">
                <input type="checkbox" v-model="options.threatChecker" />
                <span class="text-sm">Threat checker</span>
            </label>
        </div>

        <!-- Run Analysis Button -->
        <button
            @click="emit('runAnalysis', { sensitivity, ...options })"
            class="btn-base btn w-full gap-2 mt-2 this:primary bg-this text-white hover:bg-this-darker focus:bg-this-darker active:bg-this-darker/90 disabled:bg-this-light dark:disabled:bg-this-darker"
        >
            <template v-if="loading">
                <div
                    class="spinner spinner-base rounded-full animate-spin ghost-spinner border-white/30 border-r-white size-4 border-2"
                ></div>
                <span>Analyzing...</span>
            </template>
            <template v-else>
                <font-awesome-icon icon="fa-solid fa-magnifying-glass" />
                Run Analysis
            </template>
        </button>
    </div>
</template>
