<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Briefcase, Settings, UserCircle, Edit3 } from 'lucide-vue-next';
import type { UserProfile } from '../types';

const emit = defineEmits<{
  (e: 'start', jd: string, type: string): void;
  (e: 'editProfile'): void;
}>();

const jd = ref('');
const type = ref('General');
const profile = ref<UserProfile | null>(null);

onMounted(() => {
  const saved = localStorage.getItem('userProfile');
  if (saved) {
    try { profile.value = JSON.parse(saved); } catch (e) {}
  }
});

const handleSubmit = () => {
  if (jd.value.trim() && profile.value) {
    emit('start', jd.value, type.value);
  }
};
</script>

<template>
  <div class="max-w-3xl mx-auto p-8 bg-white rounded-2xl shadow-sm border border-gray-100">
    <div class="mb-8 text-center">
      <h2 class="text-3xl font-bold text-gray-900 mb-2">Setup Mock Interview</h2>
      <p class="text-gray-500">Provide your details to tailor the interview to your needs.</p>
    </div>

    <div v-if="!profile" class="text-center py-8 bg-gray-50 rounded-xl border border-dashed border-gray-300 mb-6">
      <UserCircle class="w-12 h-12 text-gray-400 mx-auto mb-3" />
      <h3 class="text-lg font-medium text-gray-900 mb-1">No Profile Found</h3>
      <p class="text-sm text-gray-500 mb-4">Please create your profile or upload a resume first.</p>
      <button
        @click="emit('editProfile')"
        class="px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors"
      >
        Create Profile
      </button>
    </div>

    <form v-else @submit.prevent="handleSubmit" class="space-y-6">
      <div class="bg-indigo-50 rounded-xl p-5 border border-indigo-100 flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <div class="w-12 h-12 bg-indigo-200 rounded-full flex items-center justify-center text-indigo-700 font-bold text-xl">
            {{ profile.name ? profile.name.charAt(0).toUpperCase() : 'U' }}
          </div>
          <div>
            <h3 class="font-semibold text-gray-900">{{ profile.name || 'Unnamed Profile' }}</h3>
            <p class="text-sm text-gray-600 truncate max-w-md">{{ profile.summary || 'No summary provided' }}</p>
          </div>
        </div>
        <button
          type="button"
          @click="emit('editProfile')"
          class="flex items-center px-3 py-2 text-sm font-medium text-indigo-700 bg-indigo-100 hover:bg-indigo-200 rounded-lg transition-colors"
        >
          <Edit3 class="w-4 h-4 mr-2" />
          Edit Profile
        </button>
      </div>
      
      <div>
        <label class="flex items-center text-sm font-semibold text-gray-700 mb-2">
          <Briefcase class="w-4 h-4 mr-2 text-indigo-500" />
          Job Description
        </label>
        <textarea
          required
          rows="6"
          class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all resize-none bg-gray-50/50"
          placeholder="Paste the job description here..."
          v-model="jd"
        ></textarea>
      </div>

      <div>
        <label class="flex items-center text-sm font-semibold text-gray-700 mb-2">
          <Settings class="w-4 h-4 mr-2 text-indigo-500" />
          Interview Type
        </label>
        <select
          class="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all bg-gray-50/50"
          v-model="type"
        >
          <option value="General">General / Behavioral</option>
          <option value="Technical">Technical</option>
          <option value="System Design">System Design</option>
          <option value="Product Management">Product Management</option>
        </select>
      </div>

      <button
        type="submit"
        :disabled="!jd.trim()"
        class="w-full py-4 mt-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all shadow-md hover:shadow-lg transform hover:-translate-y-0.5 disabled:transform-none disabled:shadow-none"
      >
        Start Interview
      </button>
    </form>
  </div>
</template>
