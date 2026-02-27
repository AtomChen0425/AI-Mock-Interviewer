<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Loader2, RefreshCcw, Award } from 'lucide-vue-next';
import { generateFeedback } from '../services/apiService';
import { marked } from 'marked';

const props = defineProps<{
  chatHistory: { role: string; text: string }[];
  resume: string;
  jobDescription: string;
}>();

const emit = defineEmits<{
  (e: 'restart'): void;
}>();

const feedbackHtml = ref('');
const isLoading = ref(true);

onMounted(async () => {
  try {
    let result = await generateFeedback(props.chatHistory, props.resume, props.jobDescription);
    result = result.replace(/^```(?:markdown)?\s*/i, '').replace(/```\s*$/i, '');

    feedbackHtml.value = await marked.parse(result, { 
      breaks: true, 
      gfm: true    
    });
  } catch (error) {
    console.error(error);
    feedbackHtml.value = "Sorry, there was an error generating your feedback report.";
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <div class="max-w-4xl mx-auto p-8 bg-white rounded-2xl shadow-sm border border-gray-100">
    <div class="mb-8 flex items-center justify-between border-b border-gray-100 pb-6">
      <div class="flex items-center space-x-4">
        <div class="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600">
          <Award class="w-6 h-6" />
        </div>
        <div>
          <h2 class="text-3xl font-bold text-gray-900">Interview Feedback</h2>
          <p class="text-gray-500 mt-1">Detailed analysis of your performance</p>
        </div>
      </div>
      <button
        @click="emit('restart')"
        class="flex items-center px-4 py-2 bg-gray-50 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-100 transition-colors border border-gray-200"
      >
        <RefreshCcw class="w-4 h-4 mr-2" />
        Start New Interview
      </button>
    </div>

    <div v-if="isLoading" class="flex flex-col items-center justify-center py-20 space-y-4">
      <Loader2 class="w-10 h-10 text-indigo-600 animate-spin" />
      <p class="text-gray-500 font-medium">Analyzing your responses and generating feedback...</p>
    </div>

    <div v-else class="prose prose-indigo max-w-none prose-headings:font-bold prose-h1:text-2xl prose-h2:text-xl prose-p:text-gray-600 prose-li:text-gray-600">
      <div v-html="feedbackHtml"></div>
    </div>
  </div>
</template>
