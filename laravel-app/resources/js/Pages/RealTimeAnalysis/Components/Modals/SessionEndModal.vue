<script setup>
import {
    Dialog,
    DialogPanel,
    DialogTitle,
    TransitionRoot,
    TransitionChild,
} from "@headlessui/vue";
import { computed } from "vue";

// Defines the component's props for visibility, state, and session statistics.
const props = defineProps({
    isVisible: {
        type: Boolean,
        default: false,
    },
    state: {
        type: String,
        default: "processing", // Can be 'processing' or 'finished'
    },
    // Add a prop to receive the final session stats
    stats: {
        type: Object,
        required: true,
    },
});

// Defines the custom events that this component can emit.
const emit = defineEmits(["start-new", "view-details", "close"]);

// Computed property to format the detection rate as a percentage.
const formattedDetectionRate = computed(() => {
    if (!props.stats.totalFrames) return "0.00%";
    const rate =
        (props.stats.defectiveProducts / props.stats.totalFrames) * 100;
    return `${rate.toFixed(2)}%`;
});
</script>

<template>
    <TransitionRoot appear :show="isVisible" as="template">
        <Dialog as="div" @close="() => {}" class="z-50 relative">
            <!-- Modal Overlay -->
            <TransitionChild
                as="template"
                enter="ease-out duration-300"
                enter-from="opacity-0"
                enter-to="opacity-100"
                leave="ease-in duration-200"
                leave-from="opacity-100"
                leave-to="opacity-0"
            >
                <div
                    class="fixed inset-0 bg-gray-900/50 dark:bg-black/30 backdrop-blur"
                />
            </TransitionChild>

            <div class="fixed inset-0 overflow-y-auto">
                <div
                    class="flex justify-center items-center p-4 min-h-full text-center"
                >
                    <!-- Modal Panel -->
                    <TransitionChild
                        as="template"
                        enter="ease-out duration-300"
                        enter-from="opacity-0 scale-95"
                        enter-to="opacity-100 scale-100"
                        leave="ease-in duration-200"
                        leave-from="opacity-100 scale-100"
                        leave-to="opacity-0 scale-95"
                    >
                        <DialogPanel
                            class="bg-white dark:bg-dark-700 shadow-xl p-8 rounded-2xl w-full max-w-lg overflow-hidden text-left align-middle transition-all transform"
                        >
                            <!-- Processing State -->
                            <div
                                v-if="state === 'processing'"
                                class="text-center"
                            >
                                <div
                                    class="flex justify-center items-center mb-4"
                                >
                                    <div
                                        class="border-b-4 border-blue-500 rounded-full w-16 h-16 animate-spin"
                                    ></div>
                                </div>
                                <h3
                                    class="font-semibold text-gray-800 dark:text-gray-200 text-xl"
                                >
                                    Finalizing Session
                                </h3>
                                <p
                                    class="mt-2 text-gray-500 dark:text-gray-400"
                                >
                                    Please wait while we generate the session
                                    report...
                                </p>
                            </div>

                            <!-- Finished State -->
                            <div
                                v-if="state === 'finished'"
                                class="text-center"
                            >
                                <DialogTitle
                                    as="h3"
                                    class="font-medium text-gray-900 text-lg leading-6"
                                >
                                    <!-- Animated Checkmark SVG -->
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        viewBox="0 0 154 154"
                                        fill="none"
                                        class="stroke-current mx-auto size-24 text-green-500 shrink-0"
                                    >
                                        <path
                                            d="M77 141C112.346 141 141 112.346 141 77C141 41.6538 112.346 13 77 13C41.6538 13 13 41.6538 13 77C13 112.346 41.6538 141 77 141Z"
                                            stroke-width="10"
                                            class="checkmark-circle"
                                        ></path>
                                        <path
                                            d="M46 80.2444L63.9556 98.1111L107.067 55"
                                            stroke-width="10"
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            class="checkmark-tick"
                                        ></path>
                                    </svg>
                                </DialogTitle>
                                <h3
                                    class="mt-4 font-bold text-gray-800 dark:text-gray-100 text-2xl"
                                >
                                    Session Complete
                                </h3>
                                <!-- Session Stats Summary -->
                                <div
                                    class="space-y-2 mt-4 text-gray-600 dark:text-gray-300"
                                >
                                    <p>
                                        A total of
                                        <strong>{{ stats.totalFrames }}</strong>
                                        frames were analyzed.
                                    </p>
                                    <div class="flex justify-center gap-6">
                                        <span
                                            ><strong class="text-green-500">{{
                                                stats.goodProducts
                                            }}</strong>
                                            Good</span
                                        >
                                        <span
                                            ><strong class="text-red-500">{{
                                                stats.defectiveProducts
                                            }}</strong>
                                            Defects</span
                                        >
                                        <span
                                            ><strong class="text-blue-500">{{
                                                formattedDetectionRate
                                            }}</strong>
                                            Defect Rate</span
                                        >
                                    </div>
                                </div>

                                <!-- Action Buttons -->
                                <div class="flex flex-col gap-3 mt-6">
                                    <button
                                        @click="$emit('start-new')"
                                        class="gap-2 bg-this hover:bg-this-darker focus:bg-this-darker active:bg-this-darker/90 disabled:bg-this-light dark:disabled:bg-this-darker w-full text-white btn-base btn this:primary"
                                    >
                                        <font-awesome-icon
                                            icon="fa-solid fa-recycle"
                                        />
                                        Run Another Session
                                    </button>
                                    <Link :href="route('sessions.index')">
                                        <button
                                            class="gap-2 bg-gray-150 hover:bg-gray-200 focus:bg-gray-200 active:bg-gray-200/80 dark:active:bg-surface-1/90 dark:bg-surface-2 dark:hover:bg-surface-1 dark:focus:bg-surface-1 w-full text-gray-900 dark:text-dark-50 btn-base btn"
                                        >
                                            <font-awesome-icon
                                                icon="fa-solid fa-folder-open"
                                            />
                                            View Session History
                                        </button>
                                    </Link>
                                </div>
                            </div>
                        </DialogPanel>
                    </TransitionChild>
                </div>
            </div>
        </Dialog>
    </TransitionRoot>
</template>

<style scoped>
/* Keyframe animations for the SVG checkmark */
.checkmark-circle {
    stroke-dasharray: 480px, 480px;
    stroke-dashoffset: 960px;
    animation: draw-circle 1s ease-out forwards;
}

.checkmark-tick {
    stroke-dasharray: 100px, 100px;
    stroke-dashoffset: 200px;
    animation: draw-check 0.8s ease-out 0.5s forwards;
}

@keyframes draw-circle {
    to {
        stroke-dashoffset: 0;
    }
}

@keyframes draw-check {
    to {
        stroke-dashoffset: 0;
    }
}
</style>
