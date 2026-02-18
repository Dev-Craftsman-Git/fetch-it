<template>
  <div 
    v-if="message" 
    :class="[
      'fixed top-5 right-5 px-6 py-4 rounded-lg shadow-xl text-white transition-all transform duration-300 z-50',
      type === 'error' ? 'bg-red-500' : 'bg-green-500'
    ]"
    role="alert"
  >
    <div class="flex items-center space-x-3">
      <span v-if="type === 'error'" class="text-xl">⚠️</span>
      <span v-else class="text-xl">✅</span>
      <p class="font-medium">{{ message }}</p>
      <button @click="$emit('close')" class="ml-4 hover:text-gray-200">✕</button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  message: String,
  type: {
    type: String, // 'error' or 'success'
    default: 'error'
  }
})
defineEmits(['close'])
</script>
