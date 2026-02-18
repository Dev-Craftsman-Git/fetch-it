<template>
  <div v-if="file" class="w-full max-w-2xl mx-auto mt-8 animate-fade-in-up">
    <div class="bg-gray-800 p-8 rounded-2xl shadow-2xl border border-gray-700 w-full max-w-md text-center">
      <div v-if="file.thumbnail" class="mb-6 rounded-xl overflow-hidden shadow-lg">
          <img :src="file.thumbnail" alt="Thumbnail" class="w-full h-48 object-cover object-center" />
      </div>
      
      <div class="flex items-center space-x-6 mb-6">
        <div class="p-4 bg-gray-700 rounded-xl">
          <svg class="w-12 h-12 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
        </div>
        <div class="flex-1 overflow-hidden text-left">
          <h3 class="text-xl font-bold text-white truncate" :title="file.title || file.filename">{{ file.title || file.filename }}</h3>
          <p class="text-gray-400 mt-1">{{ formatSize(file.size) }}</p>
        </div>
      </div>
      
      <!-- Quality Selection -->
      <div v-if="sortedFormats.length > 0" class="mb-6 text-left">
        <label class="block text-gray-400 text-sm font-bold mb-2">Select Quality:</label>
        <div class="relative">
          <select 
            v-model="selectedFormat" 
            class="block appearance-none w-full bg-gray-700 border border-gray-600 hover:border-gray-500 px-4 py-3 pr-8 rounded-xl shadow leading-tight focus:outline-none focus:shadow-outline text-white transition-colors"
          >
            <option v-for="fmt in sortedFormats" :key="fmt.format_id" :value="fmt">
              {{ fmt.label }} ({{ fmt.ext.toUpperCase() }}) - {{ fmt.is_direct ? 'Ready' : 'High Quality (Processing)' }} [{{ formatSize(fmt.filesize) }}]
            </option>
          </select>
          <div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-400">
            <svg class="fill-current h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
          </div>
        </div>
      </div>

      <div v-if="preparing" class="flex flex-col items-center justify-center py-4 space-y-3">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
        <p class="text-green-400 font-medium">{{ processingMessage }}</p>
      </div>

      <button
        v-else
        @click="handleDownload"
        class="block w-full py-4 bg-green-600 hover:bg-green-500 text-white text-center font-bold rounded-xl shadow-lg transform hover:scale-[1.02] transition-all flex items-center justify-center space-x-2 cursor-pointer"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
        </svg>
        <span>{{ downloadButtonText }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted } from 'vue'

const props = defineProps({
  file: Object
})

const preparing = ref(false)
const processingMessage = ref("Preparing download stream...")
const selectedFormat = ref(null)

// Initialize selected format
onMounted(() => {
  if (sortedFormats.value.length > 0) {
    // Default to best direct format (usually 720p) or first available
    const bestDirect = sortedFormats.value.find(f => f.is_direct)
    selectedFormat.value = bestDirect || sortedFormats.value[0]
  }
})

// Watch for file changes to reset selection
watch(() => props.file, (newFile) => {
    if (newFile && newFile.formats && newFile.formats.length > 0) {
        // Re-sort and pick best direct
        const formats = [...newFile.formats].sort((a,b) => (parseInt(b.label) || 0) - (parseInt(a.label) || 0));
        const bestDirect = formats.find(f => f.is_direct)
        selectedFormat.value = bestDirect || formats[0]
    } else {
        selectedFormat.value = null
    }
})

const sortedFormats = computed(() => {
  if (!props.file || !props.file.formats) return []
  // Sort high to low
  return [...props.file.formats].sort((a, b) => {
      const resA = parseInt(a.label) || 0
      const resB = parseInt(b.label) || 0
      return resB - resA
  })
})

const downloadButtonText = computed(() => {
    if (selectedFormat.value && !selectedFormat.value.is_direct) {
        return "PROCESS & DOWNLOAD"
    }
    return "DOWNLOAD NOW"
})

const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return 'Unknown Size'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const handleDownload = async () => {
    if (!selectedFormat.value) {
        // Fallback for files without formats (Terabox)
        window.open(`${import.meta.env.VITE_API_URL || ''}/api/download/${props.file.fileId}`, '_blank')
        return
    }

    if (selectedFormat.value.is_direct) {
        // Use the generic download endpoint which proxies the URL inside file object
        // Wait, the file object in backend cache needs to be updated if we change format?
        // Actually, the /api/download/{id} endpoint uses the URL in FILE_CACHE.
        // But for YouTube, we have multiple URLs.
        // We should PROBABLY just open the URL directly if we have it?
        // But we want to hide the source URL and manage headers.
        // Current backend limitation: /api/download/{id} uses the single 'url' in the root of the object.
        
        // Quick fix: If it's direct and we have a specific URL for this format, 
        // we might need a way to tell the backend "Download Format X for File Y".
        // OR, we can just open the direct URL from the client if headers allow (YouTube usually expires URLs but doesn't require complex headers for playback usually).
        // Actually, YouTube URLs need to be proxied or used directly.
        
        // Better approach: Call /api/process even for direct? No, that merges.
        
        // Let's assume for now 720p is the "default" URL in the file object.
        // If user selects 720p, direct download works.
        // Use window.open for now if URL is exposed.
        if (selectedFormat.value.url) {
            window.location.href = selectedFormat.value.url + "&title=" + encodeURIComponent(props.file.title)
        } else {
             window.open(`${import.meta.env.VITE_API_URL || ''}/api/download/${props.file.fileId}`, '_blank')
        }
    } else {
        // Processed Download
        preparing.value = true
        processingMessage.value = "Processing High-Quality Stream (This may take a moment)..."
        
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/process`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: props.file.url ? props.file.url : props.file.original_url, // We need original URL. 
                    // Wait, props.file.url from resolver IS the direct link for Terabox, but for YouTube it is the video link?
                    // In UniversalDownloader.resolve:
                    // 'url': info.get('url') -> This is the direct download link for the default format.
                    // We need the ORIGINAL input URL to re-process.
                    // App.vue doesn't pass the original URL to FilePreview. 
                    // We need to fix this flow.
                    
                    // Hack: `universal_downloader` returns `webpage_url` usually.
                    // If not, we rely on the client knowing what they pasted?
                    // No, `file` object should contain `original_url`.
                    // Let's assume we update backend to return `original_url` or `webpage_url`.
                    
                    // Actually, let's use the `webpage_url` if valid, or just pass the direct URL? 
                    // `yt-dlp` needs the original YouTube link (e.g. youtube.com/watch?v=...) to process formats.
                    // The `url` field in `file` is the googlevideo.com link.
                    
                    // Let's check `universal_downloader.py`. It returns `url` from `extract_info`.
                    // `yt-dlp` info dict has `webpage_url` or `original_url`.
                    
                    url: props.file.webpage_url || props.file.url, 
                    format_id: selectedFormat.value.format_id
                })
            })
            
            const data = await response.json()
            if (data.success) {
                processingMessage.value = "Download starting..."
                window.location.href = `${import.meta.env.VITE_API_URL || ''}/api/download/${data.fileId}`
                // Reset after a bit
                setTimeout(() => preparing.value = false, 3000)
            } else {
                throw new Error(data.error)
            }
        } catch (e) {
            alert("Processing failed: " + e.message)
            preparing.value = false
        }
    }
}
</script>

<style scoped>
.animate-fade-in-up {
  animation: fadeInUp 0.5s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
