<script setup>
import { useForm } from "@inertiajs/vue3";

// --- Props ---
// This component will receive the current notification settings from the parent page.
const props = defineProps({
    settings: {
        type: Object,
        // Mock data for visualization
        default: () => ({
            email: {
                enabled: true,
                defectAlerts: true,
                dailySummary: false,
            },
            browser: {
                desktop: true,
            },
        }),
    },
});

// --- Form Management ---
// Initialize the form with the settings data.
const form = useForm({
    email_enabled: props.settings.email.enabled,
    email_defect_alerts: props.settings.email.defectAlerts,
    email_daily_summary: props.settings.email.dailySummary,
    browser_desktop: props.settings.browser.desktop,
});

// The main "Save Settings" button is in the parent Index.vue.
</script>

<template>
    <div
        class="px-6 py-5 bg-white border border-gray-200 rounded-lg shadow-sm dark:bg-dark-800 dark:shadow-none dark:border-none"
    >
        <h2
            class="mb-1 flex items-center text-lg font-semibold text-gray-900 dark:text-dark-50"
        >
            Notification Preferences
        </h2>
        <p class="mb-6 text-xs text-gray-400 dark:text-dark-300">
            Configure when and how you receive notifications.
        </p>

        <div class="my-6 h-px bg-gray-200 dark:bg-dark-500"></div>

        <!-- Section 1: Email Notifications -->
        <div>
            <h2
                class="mb-1 flex items-center text-lg font-semibold text-gray-900 dark:text-dark-50"
            >
                Email Notifications
            </h2>
            <div class="mt-4 space-y-4">
                <!-- Enable Notifications Toggle -->
                <div class="flex items-center justify-between">
                    <div>
                        <span
                            class="mb-1 text-sm font-medium text-gray-800 dark:text-dark-100"
                            >Enable Notifications</span
                        >
                        <p class="text-xs text-gray-400 dark:text-dark-300">
                            Receive email notifications for analysis results.
                        </p>
                    </div>
                    <label
                        class="relative inline-flex items-center cursor-pointer"
                    >
                        <input
                            type="checkbox"
                            v-model="form.email_enabled"
                            class="h-6 w-12 form-switch this:primary bg-gray-300 before:bg-gray-50 checked:bg-this checked:before:bg-white dark:bg-surface-1 dark:before:bg-dark-50 dark:checked:bg-this-light dark:checked:before:bg-white focus-visible:ring-3 focus-visible:ring-this/50 dark:focus-visible:ring-this-light/50"
                        />
                    </label>
                </div>
                <!-- Defect Detection Alerts Toggle -->
                <div class="flex items-center justify-between">
                    <div>
                        <span
                            class="mb-1 text-sm font-medium text-gray-800 dark:text-dark-100"
                            >Defect Detection Alerts</span
                        >
                        <p class="text-xs text-gray-400 dark:text-dark-300">
                            Get notified immediately when defects are detected.
                        </p>
                    </div>
                    <label
                        class="relative inline-flex items-center cursor-pointer"
                    >
                        <input
                            type="checkbox"
                            v-model="form.email_defect_alerts"
                            class="h-6 w-12 form-switch this:primary bg-gray-300 before:bg-gray-50 checked:bg-this checked:before:bg-white dark:bg-surface-1 dark:before:bg-dark-50 dark:checked:bg-this-light dark:checked:before:bg-white focus-visible:ring-3 focus-visible:ring-this/50 dark:focus-visible:ring-this-light/50"
                            :disabled="!form.email_enabled"
                        />
                    </label>
                </div>
                <!-- Daily Summary Toggle -->
                <div class="flex items-center justify-between">
                    <div>
                        <span
                            class="mb-1 text-sm font-medium text-gray-800 dark:text-dark-100"
                            >Daily Summary</span
                        >
                        <p class="text-xs text-gray-400 dark:text-dark-300">
                            Receive daily analysis summary reports.
                        </p>
                    </div>
                    <label
                        class="relative inline-flex items-center cursor-pointer"
                    >
                        <input
                            type="checkbox"
                            v-model="form.email_daily_summary"
                            class="h-6 w-12 form-switch this:primary bg-gray-300 before:bg-gray-50 checked:bg-this checked:before:bg-white dark:bg-surface-1 dark:before:bg-dark-50 dark:checked:bg-this-light dark:checked:before:bg-white focus-visible:ring-3 focus-visible:ring-this/50 dark:focus-visible:ring-this-light/50"
                            :disabled="!form.email_enabled"
                        />
                    </label>
                </div>
            </div>
        </div>

        <div class="my-6 h-px bg-gray-200 dark:bg-dark-500"></div>

        <!-- Section 2: Browser Notifications -->
        <div>
            <h2
                class="mb-1 flex items-center text-lg font-semibold text-gray-900 dark:text-dark-50"
            >
                Browser Notifications
            </h2>
            <div class="mt-4 space-y-4">
                <!-- Desktop Notifications Toggle -->
                <div class="flex items-center justify-between">
                    <div>
                        <span
                            class="mb-1 text-sm font-medium text-gray-800 dark:text-dark-100"
                            >Desktop Notifications</span
                        >
                        <p class="text-xs text-gray-400 dark:text-dark-300">
                            Show browser notifications for analysis completion.
                        </p>
                    </div>
                    <label
                        class="relative inline-flex items-center cursor-pointer"
                    >
                        <input
                            type="checkbox"
                            v-model="form.browser_desktop"
                            class="h-6 w-12 form-switch this:primary bg-gray-300 before:bg-gray-50 checked:bg-this checked:before:bg-white dark:bg-surface-1 dark:before:bg-dark-50 dark:checked:bg-this-light dark:checked:before:bg-white focus-visible:ring-3 focus-visible:ring-this/50 dark:focus-visible:ring-this-light/50"
                        />
                    </label>
                </div>
            </div>
        </div>
    </div>
</template>
