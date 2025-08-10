<script setup>
import { ref, computed, reactive, onMounted, watch } from "vue"; // Import onMounted and watch

// --- Import Components & Utils ---
import AccountSettings from "./Components/AccountSettings.vue";
import DetectionSettings from "./Components/DetectionSettings.vue";
import AdvancedSettings from "./Components/AdvancedSettings.vue";
import ConfirmationModal from "./Components/Modals/ConfirmationModal.vue";
import { successToast } from "@/utils/swal";

// --- State ---
const activeTab = ref("account");
const isResetModalVisible = ref(false);
const isSaving = ref(false);

// NEW: A ref to store the "clean" state of the settings.
const pristineSettings = ref("");

// --- Default Settings Data ---
const defaultSettings = {
    detection: {
        anomalyThreshold: 0.75,
        defectThreshold: 0.85,
        exportFormat: "pdf",
    },
    advanced: {
        maxConcurrentAnalyses: 2,
        cacheDuration: 24,
    },
};

// --- Live Settings Data ---
const settings = reactive({
    account: {
        name: "navin",
        username: "navin",
    },
    detection: JSON.parse(JSON.stringify(defaultSettings.detection)),
    advanced: {
        systemInfo: {
            "System Version": "v2.0.0",
            "API Status": "Connected",
            "Models Loaded": "Yes",
            Database: "Connected",
        },
        performance: JSON.parse(JSON.stringify(defaultSettings.advanced)),
    },
});

// NEW: A computed property to check if there are any unsaved changes.
const hasUnsavedChanges = computed(() => {
    // It compares the stringified version of the current settings
    // with the pristine (last saved) version.
    return JSON.stringify(settings) !== pristineSettings.value;
});

// NEW: A helper function to update our "clean" snapshot.
const updatePristineState = () => {
    pristineSettings.value = JSON.stringify(settings);
};

// --- Watchers ---
// UPDATED: A deep watcher now explicitly checks for changes.
watch(
    () => JSON.stringify(settings),
    (newSettingsString) => {
        hasUnsavedChanges.value = newSettingsString !== pristineSettings.value;
    }
);

// --- Lifecycle Hooks ---
// When the component is first mounted, take the initial snapshot.
onMounted(() => {
    const storedSettings = localStorage.getItem("userSettings");
    if (storedSettings) {
        console.log("Found stored settings, loading...");
        const parsedSettings = JSON.parse(storedSettings);
        settings.detection =
            parsedSettings.detection || defaultSettings.detection;
        settings.advanced.performance =
            parsedSettings.advanced?.performance ||
            defaultSettings.advanced.performance;
    }
    updatePristineState();
});

// An array to define the tabs, making the template cleaner.
const tabs = [
    {
        id: "account",
        name: "Account",
        component: AccountSettings,
        icon: "fa-solid fa-user",
    },
    {
        id: "detection",
        name: "Detection Settings",
        component: DetectionSettings,
        icon: "fa-solid fa-magnifying-glass",
    },
    {
        id: "advanced",
        name: "Advanced",
        component: AdvancedSettings,
        icon: "fa-solid fa-gear",
    },
];

const activeTabComponent = computed(() => {
    return tabs.find((tab) => tab.id === activeTab.value)?.component;
});

const activeTabProps = computed(() => {
    switch (activeTab.value) {
        case "account":
            return { user: settings.account };
        case "detection":
            return {
                settings: settings.detection,
                "onUpdate:settings": (newDetectionSettings) => {
                    settings.detection = newDetectionSettings;
                },
            };
        case "advanced":
            return {
                settings: settings.advanced,
                "onUpdate:settings": (newAdvancedSettings) => {
                    settings.advanced = newAdvancedSettings;
                },
            };
        default:
            return {};
    }
});

// --- Event Handlers ---
const saveSettings = () => {
    isSaving.value = true;
    console.log("Saving settings:", JSON.parse(JSON.stringify(settings)));

    setTimeout(() => {
        localStorage.setItem("userSettings", JSON.stringify(settings));
        isSaving.value = false;
        successToast("Settings saved successfully!");
        // After a successful save, update the pristine state to the new current state.
        updatePristineState();
        console.log("Settings saved successfully.");
    }, 1500);
};

const resetToDefaults = () => {
    // When resetting, we just revert the live settings object.
    // The `hasUnsavedChanges` computed property will automatically detect this change.
    settings.detection = JSON.parse(JSON.stringify(defaultSettings.detection));
    settings.advanced.performance = JSON.parse(
        JSON.stringify(defaultSettings.advanced.performance)
    );
};

// NOTE: The ConfirmationModal is now only used for the "Danger Zone" actions if you wish.
// The main "Reset to Defaults" button now works instantly, and the user can just save the result.
const handleClearData = () => {
    console.log("EVENT: Clear all analysis data");
};

const handleResetSettings = () => {
    console.log("EVENT: Reset all settings");
};
</script>

<template>
    <div>
        <!-- Tab Navigation -->
        <div class="mb-6">
            <div
                class="flex flex-col gap-4 md:flex-row md:justify-between md:items-end md:border-b md:border-gray-200 md:dark:border-dark-700"
            >
                <!-- Mobile version -- Dropdown -->
                <div class="md:hidden">
                    <label for="tabs" class="sr-only">Select a tab</label>
                    <div class="input-root undefined">
                        <div class="input-wrapper relative">
                            <select
                                id="tabs"
                                v-model="activeTab"
                                class="drop-down-tab form-select-base form-select block w-full mt-1 text-sm ltr:pr-9 rtl:pl-9 peer border-gray-300 hover:border-gray-400 focus:border-primary-600 dark:border-dark-450 dark:hover:border-dark-400 dark:focus:border-primary-500"
                            >
                                <option
                                    v-for="tab in tabs"
                                    :key="tab.id"
                                    :value="tab.id"
                                >
                                    {{ tab.name }}
                                </option>
                            </select>
                            <div
                                class="suffix ltr:right-0 rtl:left-0 pointer-events-none absolute top-0 flex h-full w-9 items-center justify-center transition-colors text-gray-400 peer-focus:text-primary-600 dark:text-dark-300 dark:peer-focus:text-primary-500"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    viewBox="0 0 20 20"
                                    fill="currentColor"
                                    aria-hidden="true"
                                    data-slot="icon"
                                    class="w-2/3"
                                >
                                    <path
                                        fill-rule="evenodd"
                                        d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z"
                                        clip-rule="evenodd"
                                    ></path>
                                </svg>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Desktop version -- Tabs -->
                <div class="hidden md:block">
                    <nav class="flex -mb-px space-x-6" aria-label="Tabs">
                        <button
                            v-for="tab in tabs"
                            :key="tab.id"
                            @click="activeTab = tab.id"
                            class="btn-base shrink-0 gap-2"
                            :class="[
                                activeTab === tab.id
                                    ? 'whitespace-nowrap border-b-2 px-3 py-2 font-medium  border-primary-600 text-primary-600 dark:border-primary-500 dark:text-primary-400'
                                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 dark:text-dark-300 dark:hover:text-dark-100 dark:hover:border-dark-500',
                                'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm',
                            ]"
                        >
                            <font-awesome-icon :icon="tab.icon" />
                            {{ tab.name }}
                        </button>
                    </nav>
                </div>

                <!-- UPDATED: Action buttons are now conditional -->
                <div
                    v-if="hasUnsavedChanges"
                    class="max-md:hidden flex items-center self-end gap-3 md:self-auto md:pb-2"
                >
                    <button
                        @click="resetToDefaults"
                        class="btn-base btn gap-2 bg-gray-150 text-gray-900 hover:bg-gray-200 focus:bg-gray-200 active:bg-gray-200/80 dark:bg-surface-2 dark:text-dark-50 dark:hover:bg-surface-1 dark:focus:bg-surface-1 dark:active:bg-surface-1/90"
                    >
                        <font-awesome-icon
                            icon="fa-solid fa-arrow-rotate-left"
                        />
                        Reset Changes
                    </button>
                    <button
                        @click="saveSettings"
                        :disabled="isSaving"
                        class="btn-base btn gap-2 this:primary bg-this text-white hover:bg-this-darker focus:bg-this-darker active:bg-this-darker/90 disabled:bg-this-light dark:disabled:bg-this-darker w-36"
                    >
                        <span
                            v-if="isSaving"
                            class="flex items-center justify-center gap-2"
                        >
                            <div
                                class="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"
                            ></div>
                            Saving...
                        </span>
                        <span v-else class="flex items-center gap-2">
                            <font-awesome-icon icon="fa-solid fa-floppy-disk" />
                            Save Settings
                        </span>
                    </button>
                </div>
            </div>
        </div>

        <!-- Dynamic Tab Content -->
        <div>
            <keep-alive>
                <component
                    :is="activeTabComponent"
                    v-bind="activeTabProps"
                    @clear-data="handleClearData"
                    @reset-settings="handleResetSettings"
                />
            </keep-alive>
        </div>

        <!-- UPDATED: Small Screen Buttons are now conditional -->
        <div
            v-if="hasUnsavedChanges"
            class="md:hidden mt-6 pt-6 flex justify-end items-center gap-3 border-t border-gray-200 dark:border-dark-700"
        >
            <button
                @click="resetToDefaults"
                class="btn-base btn gap-2 bg-gray-150 text-gray-900 hover:bg-gray-200 focus:bg-gray-200 active:bg-gray-200/80 dark:bg-surface-2 dark:text-dark-50 dark:hover:bg-surface-1 dark:focus:bg-surface-1 dark:active:bg-surface-1/90"
            >
                <font-awesome-icon icon="fa-solid fa-arrow-rotate-left" />
                Reset Changes
            </button>
            <button
                @click="saveSettings"
                :disabled="isSaving"
                class="btn-base btn gap-2 this:primary bg-this text-white hover:bg-this-darker focus:bg-this-darker active:bg-this-darker/90 disabled:bg-this-light dark:disabled:bg-this-darker w-36"
            >
                <span
                    v-if="isSaving"
                    class="flex items-center justify-center gap-2"
                >
                    <div
                        class="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"
                    ></div>
                    Saving...
                </span>
                <span v-else class="flex items-center gap-2">
                    <font-awesome-icon icon="fa-solid fa-floppy-disk" />
                    Save Settings
                </span>
            </button>
        </div>

        <!-- This modal can now be repurposed for the "Danger Zone" actions if needed -->
        <ConfirmationModal
            :show="isResetModalVisible"
            title="Reset All Settings?"
            message="Are you sure you want to reset all detection and advanced settings to their default values? This action cannot be undone."
            confirm-text="Yes, Reset Settings"
            variant="error"
            icon="fa-solid fa-clock-rotate-left"
            @close="isResetModalVisible = false"
            @confirm="handleConfirmReset"
        />
    </div>
</template>

<style scoped>
.dark .drop-down-tab {
    --bg-color: rgb(21, 22, 26);
}

.drop-down-tab {
    --bg-color: rgb(255, 255, 255);
}
</style>
