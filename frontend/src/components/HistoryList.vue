<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Clock, ChevronRight, Trash2, Briefcase, Calendar } from 'lucide-vue-next';
import type { InterviewRecord } from '../types';

const emit = defineEmits<{
  (e: 'view', id: string): void;
}>();

const records = ref<InterviewRecord[]>([]);

onMounted(() => {
  loadRecords();
});

const loadRecords = () => {
  const saved = localStorage.getItem('interviewHistory');
  if (saved) {
    try {
      records.value = JSON.parse(saved).sort((a: InterviewRecord, b: InterviewRecord) => new Date(b.date).getTime() - new Date(a.date).getTime());
    } catch (e) {
      console.error("Failed to parse history", e);
    }
  }
};

const deleteRecord = (id: string, event: Event) => {
  event.stopPropagation();
  if (confirm("Are you sure you want to delete this interview record?")) {
    records.value = records.value.filter(r => r.id !== id);
    localStorage.setItem('interviewHistory', JSON.stringify(records.value));
  }
};

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};
</script>

<template>
  <div class="max-w-4xl mx-auto p-8 bg-white rounded-2xl shadow-sm border border-gray-100">
    <div class="mb-8 flex items-center space-x-4 border-b border-gray-100 pb-6">
      <div class="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600">
        <Clock class="w-6 h-6" />
      </div>
      <div>
        <h2 class="text-3xl font-bold text-gray-900">Interview History</h2>
        <p class="text-gray-500 mt-1">Review your past mock interviews and feedback</p>
      </div>
    </div>

    <div v-if="records.length === 0" class="text-center py-16 bg-gray-50 rounded-xl border border-dashed border-gray-300">
      <Clock class="w-12 h-12 text-gray-400 mx-auto mb-3" />
      <h3 class="text-lg font-medium text-gray-900 mb-1">No History Yet</h3>
      <p class="text-sm text-gray-500">Complete a mock interview to see your records here.</p>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="record in records"
        :key="record.id"
        @click="emit('view', record.id)"
        class="group relative flex flex-col sm:flex-row sm:items-center justify-between p-6 bg-white border border-gray-200 rounded-xl hover:border-indigo-300 hover:shadow-md transition-all cursor-pointer"
      >
        <div class="flex-1 pr-8">
          <div class="flex items-center space-x-3 mb-2">
            <span class="px-2.5 py-1 bg-indigo-50 text-indigo-700 text-xs font-semibold rounded-md border border-indigo-100">
              {{ record.type }}
            </span>
            <div class="flex items-center text-sm text-gray-500">
              <Calendar class="w-4 h-4 mr-1.5" />
              {{ formatDate(record.date) }}
            </div>
            <span v-if="!record.feedbackHtml" class="px-2.5 py-1 bg-yellow-50 text-yellow-700 text-xs font-semibold rounded-md border border-yellow-100">
              Feedback Pending
            </span>
          </div>
          <div class="flex items-start">
            <Briefcase class="w-5 h-5 text-gray-400 mr-2 mt-0.5 shrink-0" />
            <p class="text-gray-900 font-medium line-clamp-2 text-sm leading-relaxed">
              {{ record.jobDescription }}
            </p>
          </div>
        </div>
        
        <div class="mt-4 sm:mt-0 flex items-center justify-end space-x-4 shrink-0">
          <button
            @click="(e) => deleteRecord(record.id, e)"
            class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
            title="Delete Record"
          >
            <Trash2 class="w-5 h-5" />
          </button>
          <div class="w-10 h-10 rounded-full bg-gray-50 group-hover:bg-indigo-50 flex items-center justify-center transition-colors">
            <ChevronRight class="w-5 h-5 text-gray-400 group-hover:text-indigo-600 transition-colors" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
