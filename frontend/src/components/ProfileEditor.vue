<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { Plus, Trash2, UploadCloud, Save, Loader2, User, Briefcase, GraduationCap } from 'lucide-vue-next';
import type { UserProfile, WorkExperience, Education } from '../types';
import { parseResumeToProfile } from '../services/apiService';

const emit = defineEmits<{
  (e: 'save'): void;
}>();

const emptyProfile: UserProfile = {
  name: '', email: '', phone: '', summary: '', skills: '', experience: [], education: []
};

const profile = ref<UserProfile>(JSON.parse(JSON.stringify(emptyProfile)));
const isParsing = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);

onMounted(() => {
  const saved = localStorage.getItem('userProfile');
  if (saved) {
    try { profile.value = JSON.parse(saved); } catch (e) {}
  }
});

const handleSave = () => {
  localStorage.setItem('userProfile', JSON.stringify(profile.value));
  emit('save');
};

const handleFileUpload = async (e: Event) => {
  const target = e.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  isParsing.value = true;
  const reader = new FileReader();
  reader.onload = async () => {
    const base64 = (reader.result as string).split(',')[1];
    const parsed = await parseResumeToProfile(base64, file.type);
    if (parsed) {
      profile.value = parsed;
    } else {
      alert("Failed to parse resume.");
    }
    isParsing.value = false;
    if (fileInputRef.value) fileInputRef.value.value = '';
  };
  reader.readAsDataURL(file);
};

const addExperience = () => {
  profile.value.experience.push({ id: Math.random().toString(), title: '', company: '', location: '', startDate: '', endDate: '', type: '', description: '' });
};

const removeExperience = (id: string) => {
  profile.value.experience = profile.value.experience.filter(exp => exp.id !== id);
};

const addEducation = () => {
  profile.value.education.push({ id: Math.random().toString(), school: '', degree: '', field: '', startDate: '', endDate: '' });
};

const removeEducation = (id: string) => {
  profile.value.education = profile.value.education.filter(edu => edu.id !== id);
};
</script>

<template>
  <div class="max-w-5xl mx-auto flex flex-col md:flex-row gap-8">
    <!-- Left Sidebar -->
    <div class="w-full md:w-64 shrink-0">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sticky top-24">
        <div class="flex flex-col items-center text-center mb-6">
          <div class="w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600 font-bold text-3xl mb-3">
            {{ profile.name ? profile.name.charAt(0).toUpperCase() : 'U' }}
          </div>
          <h3 class="font-bold text-gray-900 text-lg">{{ profile.name || 'Your Name' }}</h3>
          <p class="text-sm text-gray-500">{{ profile.email || 'Email not set' }}</p>
        </div>

        <div class="mt-8 pt-6 border-t border-gray-100">
          <button
            @click="fileInputRef?.click()"
            :disabled="isParsing"
            class="w-full flex items-center justify-center px-4 py-2 bg-white border border-gray-200 hover:bg-gray-50 text-gray-700 rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
          >
            <Loader2 v-if="isParsing" class="w-4 h-4 mr-2 animate-spin" />
            <UploadCloud v-else class="w-4 h-4 mr-2" />
            {{ isParsing ? 'Parsing...' : 'Upload Resume' }}
          </button>
          <input type="file" ref="fileInputRef" class="hidden" accept=".pdf,.doc,.docx" @change="handleFileUpload" />
          <p class="text-xs text-gray-400 mt-2 text-center">Upload PDF/DOCX to autofill</p>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 space-y-6">
      <!-- Basic Info -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <h3 class="text-xl font-bold text-gray-900 mb-6 flex items-center">
          <User class="w-5 h-5 mr-2 text-indigo-500" /> Basic Information
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <input type="text" v-model="profile.name" class="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input type="email" v-model="profile.email" class="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Phone</label>
            <input type="text" v-model="profile.phone" class="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500" />
          </div>
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-1">Professional Summary</label>
            <textarea rows="3" v-model="profile.summary" class="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 resize-none"></textarea>
          </div>
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-1">Skills (comma separated)</label>
            <textarea rows="2" v-model="profile.skills" class="w-full px-4 py-2 rounded-lg border border-gray-200 focus:ring-2 focus:ring-indigo-500 resize-none"></textarea>
          </div>
        </div>
      </div>

      <!-- Work Experience -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-bold text-gray-900 flex items-center">
            <Briefcase class="w-5 h-5 mr-2 text-indigo-500" /> Work Experience
          </h3>
          <button @click="addExperience" class="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors">
            <Plus class="w-5 h-5" />
          </button>
        </div>
        <div class="space-y-8">
          <div v-for="exp in profile.experience" :key="exp.id" class="relative pl-6 border-l-2 border-gray-100 pb-6 last:pb-0">
            <div class="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-white border-2 border-indigo-500"></div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Job Title</label>
                <input type="text" v-model="exp.title" class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Company</label>
                <input type="text" v-model="exp.company" class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs font-medium text-gray-500 mb-1">Start Date</label>
                  <input type="text" placeholder="e.g. Jan 2020" v-model="exp.startDate" class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-500" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-500 mb-1">End Date</label>
                  <input type="text" placeholder="e.g. Present" v-model="exp.endDate" class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-500" />
                </div>
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Location / Type</label>
                <div class="flex space-x-2">
                  <input type="text" placeholder="Location" v-model="exp.location" class="w-1/2 px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-500" />
                  <input type="text" placeholder="Type (e.g. Full-time)" v-model="exp.type" class="w-1/2 px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-500" />
                </div>
              </div>
              <div class="md:col-span-2">
                <label class="block text-xs font-medium text-gray-500 mb-1">Description</label>
                <textarea rows="4" v-model="exp.description" class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 resize-none"></textarea>
              </div>
            </div>
            <button @click="removeExperience(exp.id)" class="absolute top-0 right-0 p-2 text-gray-400 hover:text-red-500 transition-colors">
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
          <p v-if="profile.experience.length === 0" class="text-sm text-gray-500 italic">No work experience added yet.</p>
        </div>
      </div>

      <!-- Education -->
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <div class="flex items-center justify-between mb-6">
          <h3 class="text-xl font-bold text-gray-900 flex items-center">
            <GraduationCap class="w-5 h-5 mr-2 text-indigo-500" /> Education
          </h3>
          <button @click="addEducation" class="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors">
            <Plus class="w-5 h-5" />
          </button>
        </div>
        <div class="space-y-8">
          <div v-for="edu in profile.education" :key="edu.id" class="relative pl-6 border-l-2 border-gray-100 pb-6 last:pb-0">
            <div class="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-white border-2 border-indigo-500"></div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">School / University</label>
                <input type="text" v-model="edu.school" class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Degree</label>
                <input type="text" v-model="edu.degree" class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div>
                <label class="block text-xs font-medium text-gray-500 mb-1">Field of Study</label>
                <input type="text" v-model="edu.field" class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-500" />
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs font-medium text-gray-500 mb-1">Start Date</label>
                  <input type="text" placeholder="e.g. 2018" v-model="edu.startDate" class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-500" />
                </div>
                <div>
                  <label class="block text-xs font-medium text-gray-500 mb-1">End Date</label>
                  <input type="text" placeholder="e.g. 2022" v-model="edu.endDate" class="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-500" />
                </div>
              </div>
            </div>
            <button @click="removeEducation(edu.id)" class="absolute top-0 right-0 p-2 text-gray-400 hover:text-red-500 transition-colors">
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
          <p v-if="profile.education.length === 0" class="text-sm text-gray-500 italic">No education added yet.</p>
        </div>
      </div>

      <div class="flex justify-end pt-4">
        <button @click="handleSave" class="flex items-center px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition-all shadow-sm">
          <Save class="w-5 h-5 mr-2" /> Save Profile
        </button>
      </div>
    </div>
  </div>
</template>
