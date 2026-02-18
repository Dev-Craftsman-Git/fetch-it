<template>
  <div class="min-h-screen bg-gray-900 text-gray-100 flex flex-col font-sans selection:bg-blue-500 selection:text-white">
    <!-- Navbar -->
    <nav class="w-full p-6 border-b border-gray-800 backdrop-blur-md bg-gray-900/80 sticky top-0 z-40">
      <div class="max-w-7xl mx-auto flex justify-between items-center">
        <div class="flex items-center space-x-2">
          <div class="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"></path>
            </svg>
          </div>
          <span class="text-2xl font-black bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">FETCH IT</span>
        </div>
        <div class="text-sm text-gray-400 hidden sm:block">v1.0.0</div>
      </div>
    </nav>

    <!-- Main Content -->
    <main class="flex-grow flex flex-col items-center justify-center p-6 relative overflow-hidden">
      <!-- Background Decorations -->
      <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
        <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl animate-pulse delay-700"></div>
      </div>

      <div class="relative z-10 w-full max-w-4xl flex flex-col items-center">
        <h1 class="text-6xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-500 to-pink-500 tracking-tight" style="filter: drop-shadow(0 0 20px rgba(168,85,247,0.5));">
        FETCH IT
      </h1>
      <p class="mt-6 text-xl text-gray-300 max-w-2xl mx-auto leading-relaxed">
        The Ultimate Universal Media Downloader. <br>
        <span class="text-blue-400">YouTube</span>, <span class="text-purple-400">Terabox</span>, <span class="text-pink-400">Instagram</span>, <span class="text-green-400">Twitter</span> & more.
      </p>

        <LinkInput ref="linkInputRef" @submit="fetchFile" :loading="loading" />
        
        <FilePreview v-if="file" :file="file" />
      </div>
    </main>

    <!-- Footer -->
    <footer class="w-full p-8 border-t border-gray-800 bg-gray-900 z-10 text-center">
      <p class="text-gray-500 text-sm mb-2">
        For personal files only. Respect copyright. We do not store files. All downloads streamed directly from source.
      </p>
      <p class="text-gray-600 text-xs">
        DMCA: abuse@yourdomain.com
      </p>
    </footer>

    <StatusToast 
      v-if="toast.message" 
      :message="toast.message" 
      :type="toast.type" 
      @close="toast.message = null" 
    />
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import LinkInput from './components/LinkInput.vue'
import FilePreview from './components/FilePreview.vue'
import StatusToast from './components/StatusToast.vue'

const loading = ref(false)
const file = ref(null)
const toast = reactive({
  message: null,
  type: 'error'
})

const linkInputRef = ref(null)

const fetchFile = async (payload) => {
  const { url, cookie } = typeof payload === 'string' ? { url: payload } : payload
  
  loading.value = true
  file.value = null
  toast.message = null

  try {
    const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/resolve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ url, cookie })
    })
    
    const data = await response.json()
    
    if (data.success) {
      file.value = data
      showToast('File resolved successfully!', 'success')
    } else {
      if (data.error === 'LOGIN_REQUIRED') {
         showToast("Login Required! Please paste your 'ndus' cookie below.", 'error')
         if (linkInputRef.value) {
             linkInputRef.value.showAdvanced = true
         }
      } else {
         throw new Error(data.error || 'Failed to resolve link')
      }
    }
  } catch (err) {
    showToast(err.message, 'error')
  } finally {
    loading.value = false
  }
}

const showToast = (message, type = 'error') => {
  toast.message = message
  toast.type = type
  setTimeout(() => {
    toast.message = null
  }, 5000)
}
</script>

<style>
body {
  @apply bg-gray-900;
}
</style>
