<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Loader2, RefreshCcw, Award } from 'lucide-vue-next';
import { generateFeedback } from '../services/apiService';
import { marked } from 'marked';
import type { InterviewRecord } from '../types';

const props = defineProps<{
  recordId: string;
}>();

const emit = defineEmits<{
  (e: 'restart'): void;
}>();
const feedbackHtml = ref('');
const isLoading = ref(true);
const error = ref(false);
const record = ref<InterviewRecord | null>(null);
const activeTab = ref<'feedback' | 'chat' | 'details'>('feedback');
const loadAndGenerate = async () => {
  isLoading.value = true;
  error.value = false;
  
  const saved = localStorage.getItem('interviewHistory');
  if (saved) {
    try {
      const records: InterviewRecord[] = JSON.parse(saved);
      const found = records.find(r => r.id === props.recordId);
      if (found) {
        record.value = found;
        
        if (found.feedbackHtml) {
          feedbackHtml.value = found.feedbackHtml;
          isLoading.value = false;
          return;
        }
        
        // Generate feedback if not present
        try {
          const result = await generateFeedback(found.chatHistory, found.resumeContext, found.jobDescription);
          const html = await marked(result);
          feedbackHtml.value = html;
          
          // Save back to local storage
          found.feedbackHtml = html;
          localStorage.setItem('interviewHistory', JSON.stringify(records));
        } catch (err) {
          console.error(err);
          error.value = true;
        }
      } else {
        error.value = true;
      }
    } catch (e) {
      console.error("Failed to parse history", e);
      error.value = true;
    }
  } else {
    error.value = true;
  }
  
  isLoading.value = false;
};

onMounted(() => {
  loadAndGenerate();
});
const handleRegenerate = () => {
  if (record.value) {
    record.value.feedbackHtml = undefined; // Force regeneration
    loadAndGenerate();
  }
};
const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};
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

    <div v-else-if="error" class="flex flex-col items-center justify-center py-20 space-y-4 text-center">
      <AlertCircle class="w-12 h-12 text-red-500 mb-2" />
      <h3 class="text-xl font-bold text-gray-900">Failed to Generate Feedback</h3>
      <p class="text-gray-500 max-w-md">There was an error generating your feedback report. This might be due to a network issue or API limit.</p>
      <button
        @click="handleRegenerate"
        class="mt-4 flex items-center px-6 py-3 bg-indigo-600 text-white rounded-xl font-semibold hover:bg-indigo-700 transition-colors shadow-sm"
      >
        <RefreshCcw class="w-5 h-5 mr-2" />
        Try Again
      </button>
    </div>

    <div v-else-if="record">
      <div class="flex space-x-1 border-b border-gray-200 mb-8">
        <button
          @click="activeTab = 'feedback'"
          :class="['px-4 py-3 text-sm font-medium border-b-2 transition-colors flex items-center', activeTab === 'feedback' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300']"
        >
          <Award class="w-4 h-4 mr-2" />
          Feedback Report
        </button>
        <button
          @click="activeTab = 'chat'"
          :class="['px-4 py-3 text-sm font-medium border-b-2 transition-colors flex items-center', activeTab === 'chat' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300']"
        >
          <MessageSquare class="w-4 h-4 mr-2" />
          Chat History
        </button>
        <button
          @click="activeTab = 'details'"
          :class="['px-4 py-3 text-sm font-medium border-b-2 transition-colors flex items-center', activeTab === 'details' ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300']"
        >
          <FileText class="w-4 h-4 mr-2" />
          Interview Details
        </button>
      </div>

      <div v-if="activeTab === 'feedback'" class="prose prose-indigo max-w-none prose-headings:font-bold prose-h1:text-2xl prose-h2:text-xl prose-p:text-gray-600 prose-li:text-gray-600">
        <div v-html="feedbackHtml"></div>
      </div>

      <div v-else-if="activeTab === 'chat'" class="space-y-6 bg-gray-50 p-6 rounded-2xl border border-gray-100">
        <div
          v-for="(msg, index) in record.chatHistory"
          :key="index"
          :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
        >
          <div :class="['flex max-w-[80%]', msg.role === 'user' ? 'flex-row-reverse' : 'flex-row']">
            <div :class="['w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-1', msg.role === 'user' ? 'bg-indigo-100 text-indigo-600 ml-3' : 'bg-gray-200 text-gray-600 mr-3']">
              <User v-if="msg.role === 'user'" class="w-5 h-5" />
              <Bot v-else class="w-5 h-5" />
            </div>
            <div
              :class="[
                'p-4 rounded-2xl text-sm leading-relaxed',
                msg.role === 'user' 
                  ? 'bg-indigo-600 text-white rounded-tr-none' 
                  : 'bg-white border border-gray-200 text-gray-800 rounded-tl-none shadow-sm'
              ]"
            >
              {{ msg.text }}
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'details'" class="space-y-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="bg-gray-50 p-5 rounded-xl border border-gray-100">
            <h4 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">Date & Time</h4>
            <p class="text-gray-900 font-medium">{{ formatDate(record.date) }}</p>
          </div>
          <div class="bg-gray-50 p-5 rounded-xl border border-gray-100">
            <h4 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">Interview Type</h4>
            <p class="text-gray-900 font-medium">{{ record.type }}</p>
          </div>
        </div>
        
        <div class="bg-gray-50 p-6 rounded-xl border border-gray-100">
          <h4 class="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Job Description</h4>
          <p class="text-gray-700 whitespace-pre-wrap text-sm leading-relaxed">{{ record.jobDescription }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
