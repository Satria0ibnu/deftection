<script setup>
import { computed, onMounted, onUnmounted } from "vue";

// The component accepts the image URL as a prop.
// If the URL is null, the modal is hidden.
const props = defineProps({
    imageUrl: {
        type: String,
        default: null,
    },
});

// The component emits a 'close' event to the parent.
const emit = defineEmits(["close"]);

// A computed property to determine if the modal should be visible.
const isModalOpen = computed(() => !!props.imageUrl);

// --- Event Handlers ---
const closeModal = () => {
    emit("close");
};

// Handle closing the modal with the 'Escape' key
const handleKeydown = (event) => {
    if (event.key === "Escape" && isModalOpen.value) {
        closeModal();
    }
};

onMounted(() => {
    window.addEventListener("keydown", handleKeydown);
});

onUnmounted(() => {
    window.removeEventListener("keydown", handleKeydown);
});
</script>

<template>
    <Teleport to="body">
        <transition
            enter-active-class="transition-opacity ease-in-out duration-300"
            enter-from-class="opacity-0"
            enter-to-class="opacity-100"
            leave-active-class="transition-opacity ease-in-out duration-300"
            leave-from-class="opacity-100"
            leave-to-class="opacity-0"
        >
            <div
                v-if="isModalOpen"
                @click.self="closeModal"
                class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
                role="dialog"
                aria-modal="true"
            >
                <div class="relative">
                    <img
                        :src="imageUrl"
                        alt="Zoomed Scan"
                        class="max-h-[90vh] max-w-[90vw] rounded-lg shadow-xl"
                    />
                </div>
            </div>
        </transition>
    </Teleport>
</template>
