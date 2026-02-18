<template>
  <div class="w-full max-w-2xl mx-auto">
    <div class="bg-gray-800 p-8 rounded-2xl shadow-2xl border border-gray-700">
      <h2 class="text-2xl font-bold text-center text-blue-400 mb-6">Paste Your Link</h2>
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div class="relative">
          <input 
            v-model="url" 
            type="text" 
            placeholder="Paste YouTube, Terabox, Instagram, or Twitter link..." 
            class="w-full px-6 py-4 bg-gray-900 border border-gray-600 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            :disabled="loading"
          />
          <div v-if="loading" class="absolute right-4 top-4">
            <svg class="animate-spin h-6 w-6 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        </div>

        <!-- Advanced Options Toggle -->
        <div class="text-right">
            <button type="button" @click="showAdvanced = !showAdvanced" class="text-xs text-blue-400 hover:text-blue-300 underline">
                {{ showAdvanced ? 'Hide Advanced' : 'Advanced Options (Cookie/Password)' }}
            </button>
        </div>

        <!-- Cookie Input -->
        <div v-if="showAdvanced" class="animate-fade-in-down">
            <input 
                v-model="cookie" 
                type="text" 
                placeholder="Optional: Paste 'ndus' cookie or password for blocked links..." 
                class="w-full px-4 py-2 text-sm bg-gray-900 border border-gray-700 rounded-lg text-gray-300 placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-all"
            />
        </div>

        <button 
          type="submit" 
          :disabled="loading || !isValid"
          class="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold rounded-xl transform hover:scale-[1.02] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
        >
          {{ loading ? 'Resolving...' : 'FETCH FILE' }}
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps(['loading'])
const emit = defineEmits(['submit'])

const url = ref('')
const cookie = ref('')
const showAdvanced = ref(false)

// Expose checks or methods if needed, but for now we rely on props or events?
// Actually, to open it from parent, we need to expose it.
defineExpose({ showAdvanced, cookie })

const isValid = computed(() => {
  return url.value.length > 0 && (url.value.startsWith('http://') || url.value.startsWith('https://'))
})

const handleSubmit = () => {
  if (isValid.value) {
    emit('submit', { url: url.value, cookie: cookie.value })
  }
}
</script>
