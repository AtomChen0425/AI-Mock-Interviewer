<script setup lang="ts">
import { ref } from 'vue';
import { Bot, UserCircle } from 'lucide-vue-next';
import SetupForm from './components/SetupForm.vue';
import ProfileEditor from './components/ProfileEditor.vue';
import InterviewChat from './components/InterviewChat.vue';
import FeedbackReport from './components/FeedbackReport.vue';
// ⚠️ 修改点 1：把原来从 geminiService 引入的方法，改为从你新建的 apiService 引入
import { analyzeResume } from './services/apiService'; 
import type { UserProfile } from './types';
// ⚠️ 修改点 2：删除 import type { Chat } from '@google/genai';

type AppState = 'setup' | 'interview' | 'feedback' | 'profile';

const appState = ref<AppState>('setup');
// ⚠️ 修改点 3：删除 const chatInstance = ref<Chat | null>(null);
// 新增 interviewType 用于传递给 Chat 组件
const interviewType = ref(''); 

const chatHistory = ref<{ role: string; text: string }[]>([]);
const resumeContext = ref('');
const jd = ref('');
const isStarting = ref(false);
const loadingStep = ref('');

function formatProfileForAI(profile: UserProfile): string {
  // ... (保留原有的格式化逻辑不变)
  let text = `Name: ${profile.name}\nEmail: ${profile.email}\nPhone: ${profile.phone}\n\n`;
  text += `Summary:\n${profile.summary}\n\n`;
  text += `Skills:\n${profile.skills}\n\n`;
  
  text += `Work Experience:\n`;
  profile.experience.forEach(exp => {
    text += `- ${exp.title} at ${exp.company} (${exp.location}) | ${exp.startDate} - ${exp.endDate} | ${exp.type}\n  ${exp.description}\n`;
  });
  
  text += `\nEducation:\n`;
  profile.education.forEach(edu => {
    text += `- ${edu.degree} in ${edu.field} from ${edu.school} | ${edu.startDate} - ${edu.endDate}\n`;
  });
  
  return text;
}

const handleStart = async (j: string, type: string) => {
  isStarting.value = true;
  jd.value = j;
  interviewType.value = type; // 保存面试类型
  
  try {
    const saved = localStorage.getItem('userProfile');
    if (!saved) throw new Error("Profile not found");
    const profile: UserProfile = JSON.parse(saved);
    const profileText = formatProfileForAI(profile);
    
    loadingStep.value = 'Analyzing Profile vs Job Description...';
    // ⚠️ 修改点 4：这里的 analyzeResume 现在是一个发向 FastAPI 的 HTTP 请求
    const context = await analyzeResume(profileText, j); 
    
    resumeContext.value = context;
    
    // ⚠️ 修改点 5：不再在这里创建 startInterviewChat，直接切换状态即可
    loadingStep.value = 'Preparing Interviewer...';
    appState.value = 'interview';
    
  } catch (error) {
    console.error("Failed to initialize chat:", error);
    alert("Failed to start the interview. Please check your backend connection.");
  } finally {
    isStarting.value = false;
    loadingStep.value = '';
  }
};

const handleInterviewComplete = (history: { role: string; text: string }[]) => {
  chatHistory.value = history;
  appState.value = 'feedback';
};

const handleRestart = () => {
  appState.value = 'setup';
  interviewType.value = '';
  chatHistory.value = [];
  resumeContext.value = '';
  jd.value = '';
};
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 font-sans">
     <header class="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div class="flex items-center space-x-3 cursor-pointer" @click="appState = 'setup'">
          <div class="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white shadow-sm">
            <Bot class="w-6 h-6" />
          </div>
          <h1 class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600">
            AI Mock Interviewer
          </h1>
        </div>
        <div class="flex items-center space-x-4">
          <button 
            @click="appState = 'setup'"
            :class="['text-sm font-medium transition-colors', appState === 'setup' ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-900']"
          >
            Interview
          </button>
          <button 
            @click="appState = 'profile'"
            :class="['flex items-center text-sm font-medium transition-colors', appState === 'profile' ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-900']"
          >
            <UserCircle class="w-4 h-4 mr-1" />
            My Profile
          </button>
        </div>
      </div>
    </header>
     <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div v-if="appState === 'setup'" class="relative">
        <div v-if="isStarting" class="absolute inset-0 bg-white/50 backdrop-blur-sm z-10 flex items-center justify-center rounded-2xl">
          <div class="flex flex-col items-center space-y-3">
            <div class="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin"></div>
            <p class="text-sm font-medium text-indigo-600">{{ loadingStep || 'Preparing...' }}</p>
          </div>
        </div>
        <SetupForm @start="handleStart" @editProfile="appState = 'profile'" />
      </div>
      
      <ProfileEditor v-if="appState === 'profile'" @save="appState = 'setup'" />

        <InterviewChat 
          v-if="appState === 'interview'" 
          :resumeContext="resumeContext"
          :jobDescription="jd"
          :interviewType="interviewType"
          @complete="handleInterviewComplete" 
        />

        <FeedbackReport
          v-if="appState === 'feedback'"
          :chatHistory="chatHistory"
          :resume="resumeContext"
          :jobDescription="jd"
          @restart="handleRestart"
        />
     </main>
  </div>
</template>