<script setup>
import { Link } from "@inertiajs/vue3";
import { formatDistanceToNow, format } from "date-fns";
import RowNotFound from "../../../Shared/Table/RowNotFound.vue";

// Defines the data this component receives from its parent (Dashboard/Index.vue).
const props = defineProps({
    analyses: {
        type: Array,
        default: () => [],
    },
});

// A collection of utility functions to format raw data for clean display in the table.

const formatDateSimple = (dateString) => {
    if (!dateString) return "N/A";
    try {
        const date = new Date(dateString);
        return format(date, "dd-MM-yyyy");
    } catch (error) {
        return "Invalid date";
    }
};

const formatRelativeTime = (dateString) => {
    if (!dateString) return "N/A";
    try {
        const date = new Date(dateString);
        return formatDistanceToNow(date, { addSuffix: true });
    } catch (error) {
        return "Invalid date";
    }
};

const formatDecimal = (value, defaultValue = 0, precision = 3) => {
    const num = Number(value);
    return isNaN(num) ? defaultValue : num.toFixed(precision);
};

const getStatusClass = (status) => {
    switch (status) {
        case "good":
            return "bg-green-100 text-green-800 dark:bg-green-500/10 dark:text-green-400";
        case "defect":
            return "bg-red-100 text-red-800 dark:bg-red-500/10 dark:text-red-400";
        default:
            return "bg-gray-100 text-gray-800 dark:bg-gray-500/10 dark:text-gray-400";
    }
};
</script>

<template>
    <div class="flex flex-col overflow-hidden transition-content grow">
        <div class="overflow-x-auto">
            <table
                class="table w-full min-w-full text-left rtl:text-right is-hoverable"
            >
                <thead class="group/thead table-thead">
                    <tr class="group/tr table-tr">
                        <th
                            class="group/th table-th bg-gray-200 dark:bg-dark-800 px-3 first:ltr:rounded-tl-lg last:rtl:rounded-tl-lg first:rtl:rounded-tr-lg last:ltr:rounded-tr-lg w-32 font-semibold text-gray-800 dark:text-dark-100 uppercase"
                        >
                            Image
                        </th>
                        <th
                            class="group/th table-th bg-gray-200 dark:bg-dark-800 px-3 first:ltr:rounded-tl-lg last:rtl:rounded-tl-lg first:rtl:rounded-tr-lg last:ltr:rounded-tr-lg w-28 font-semibold text-gray-800 dark:text-dark-100 uppercase"
                        >
                            Date
                        </th>
                        <th
                            class="group/th table-th bg-gray-200 dark:bg-dark-800 px-3 first:ltr:rounded-tl-lg last:rtl:rounded-tl-lg first:rtl:rounded-tr-lg last:ltr:rounded-tr-lg w-20 font-semibold text-gray-800 dark:text-dark-100 uppercase"
                        >
                            Status
                        </th>
                        <th
                            class="group/th table-th bg-gray-200 dark:bg-dark-800 px-3 first:ltr:rounded-tl-lg last:rtl:rounded-tl-lg first:rtl:rounded-tr-lg last:ltr:rounded-tr-lg w-20 font-semibold text-gray-800 dark:text-dark-100 uppercase"
                        >
                            Score
                        </th>
                        <th
                            class="group/th table-th bg-gray-200 dark:bg-dark-800 px-3 first:ltr:rounded-tl-lg last:rtl:rounded-tl-lg first:rtl:rounded-tr-lg last:ltr:rounded-tr-lg w-16 font-semibold text-gray-800 dark:text-dark-100 uppercase"
                        >
                            Actions
                        </th>
                    </tr>
                </thead>
                <tbody class="group/tbody table-tbody">
                    <tr
                        v-for="item in analyses"
                        :key="item.id"
                        class="group/tr table-tr relative border-y border-transparent border-b-gray-200 dark:border-b-dark-500"
                    >
                        <!-- Image Column with fixed width -->
                        <td
                            class="group/td table-td relative dark:bg-dark-900 py-3 pl-3 w-32"
                        >
                            <div
                                class="flex flex-col items-start gap-1 min-w-0"
                            >
                                <img
                                    class="flex-shrink-0 rounded-md w-20 h-12 object-cover"
                                    :src="item.annotated_image_url"
                                    alt="Analysis Image"
                                />
                                <p
                                    class="w-full max-w-[120px] font-medium text-gray-800 dark:text-dark-100 text-sm truncate"
                                    :title="item.filename"
                                >
                                    {{ item.filename }}
                                </p>
                            </div>
                        </td>
                        <!-- Analysis Date Column -->
                        <td
                            class="group/td table-td relative dark:bg-dark-900 py-3 pl-3 w-28"
                        >
                            <div class="min-w-0">
                                <p
                                    class="font-medium text-gray-800 dark:text-dark-100 text-sm truncate"
                                >
                                    {{ formatDateSimple(item.created_at) }}
                                </p>
                                <p
                                    class="text-gray-600 dark:text-gray-400 text-xs truncate"
                                >
                                    {{ formatRelativeTime(item.created_at) }}
                                </p>
                            </div>
                        </td>
                        <!-- Status Column -->
                        <td
                            class="group/td table-td relative dark:bg-dark-900 py-3 pl-3 w-20"
                        >
                            <span
                                class="inline-block px-2 py-1 rounded font-semibold text-xs uppercase whitespace-nowrap"
                                :class="getStatusClass(item.status)"
                            >
                                {{ item.status }}
                            </span>
                        </td>
                        <!-- Score Column -->
                        <td
                            class="group/td table-td relative dark:bg-dark-900 py-3 pl-3 w-20"
                        >
                            <p
                                class="font-mono text-gray-800 dark:text-dark-100 text-sm whitespace-nowrap"
                            >
                                {{
                                    formatDecimal(item.anomaly_score, "N/A", 3)
                                }}
                            </p>
                        </td>
                        <!-- Actions Column -->
                        <td
                            class="group/td table-td relative dark:bg-dark-900 py-3 pl-3 w-16"
                        >
                            <Link :href="item.route">
                                <div class="flex justify-center pr-3">
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        viewBox="0 0 24 24"
                                        fill="currentColor"
                                        class="size-5 text-primary-600 hover:text-primary-600/70 focus:text-primary-600/70 dark:hover:text-primary-400/70 dark:focus:text-primary-400/70 dark:text-primary-400 transition-colors duration-300 cursor-pointer"
                                    >
                                        <path
                                            d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z"
                                        />
                                        <path
                                            fill-rule="evenodd"
                                            d="M1.323 11.447C2.811 6.976 7.028 3.75 12.001 3.75c4.97 0 9.185 3.223 10.675 7.69.12.362.12.752 0 1.113-1.487 4.471-5.705 7.697-10.677 7.697-4.97 0-9.186-3.223-10.675-7.69a1.762 1.762 0 0 1 0-1.113ZM17.25 12a5.25 5.25 0 1 1-10.5 0 5.25 5.25 0 0 1 10.5 0Z"
                                            clip-rule="evenodd"
                                        />
                                    </svg>
                                </div>
                            </Link>
                        </td>
                    </tr>

                    <RowNotFound
                        v-if="analyses.length === 0"
                        label="No recent analyses found"
                    >
                        <template #description>
                            <p class="mt-1 text-xs">Try scanning a new image</p>
                        </template>
                    </RowNotFound>
                </tbody>
            </table>
        </div>
    </div>
</template>
