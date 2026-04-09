<script setup lang="ts">
import { ref ,onMounted} from 'vue';
import { Bot, UserCircle, Clock } from 'lucide-vue-next';
import SetupForm from './components/SetupForm.vue';
import ProfileEditor from './components/ProfileEditor.vue';
import InterviewChat from './components/InterviewChat.vue';
import FeedbackReport from './components/FeedbackReport.vue';
import HistoryList from './components/HistoryList.vue';
import { analyzeResume } from './services/apiService'; 
import type { UserProfile, InterviewRecord } from './types';

import { loginWithGoogle, getPaymentUrl, getToken, getUserQuota, logoutUser } from './services/apiService';
import { GoogleLogin,googleLogout } from 'vue3-google-login';

type AppState = 'setup' | 'interview' | 'feedback' | 'profile' | 'history';

const appState = ref<AppState>('setup');
const interviewType = ref(''); 

const chatHistory = ref<{ role: string; text: string }[]>([]);
const resumeContext = ref('');
const jd = ref('');
const isStarting = ref(false);
const loadingStep = ref('');
const currentRecordId = ref('');

/// Authentication & Payment State
const isAuthenticated = ref(false);
const availableQuota = ref<number | string>('?');
const showPaymentModal = ref(false);

const selectedPackage = ref<1 | 5>(1); // 默认选 1 次
const selectedProvider = ref<'stripe' | 'paypal'>('stripe'); // 默认选 Stripe
onMounted(async() => {
  if (getToken()) {
    isAuthenticated.value = true;
    const quota = await getUserQuota();
    if (quota !== null) {
      availableQuota.value = quota;
    } else {
      // 如果返回 null，说明 token 已过期或非法，自动执行退出逻辑
      handleLogout();
    }
  }
});

const handleGoogleLoginSuccess = async (response: any) => {
  try {
    const data = await loginWithGoogle(response.credential);
    if (data) {
      isAuthenticated.value = true;
      availableQuota.value = data.quota;
    } else {
      alert("Login failed, please try again.");
    }
  } catch (error) {
    console.error("Login failed", error);
    alert("An error occurred during login.");
  }
};
const handleLogout = () => {
  googleLogout(); // 清除 Google 登录会话
  logoutUser();   // 清除本地 localStorage 的 Token
  isAuthenticated.value = false;
  availableQuota.value = '?';
  appState.value = 'setup'; // 踢回首页
};
const handlePay = async () => {
  // 调用修改后的 API，传递支付网关和套餐次数
  const url = await getPaymentUrl(selectedProvider.value, selectedPackage.value);
  if (url) {
    window.location.href = url; // 跳转到 Stripe 或 PayPal 结账页面
  } else {
    alert("Payment service is currently unavailable. Please try again later.");
  }
};
function formatProfileForAI(profile: UserProfile): string {
  let text = `Name: ${profile.name}\nEmail: ${profile.email}\nPhone: ${profile.phone}\n\n`;
  text += `Summary:\n${profile.summary}\n\n`;
  text += `Skills:\n${profile.skills}\n\n`;
  
  text += `Work Experience:\n`;
  profile.workexperience.forEach(exp => {
    text += `- ${exp.title} at ${exp.company} (${exp.location}) | ${exp.startDate} - ${exp.endDate} | ${exp.type}\n  ${exp.description}\n`;
  });
  
  text += `\nProject Experience:\n`;
  profile.projectexperience.forEach(proj => {
    text += `- ${proj.title}\n | ${proj.startDate} - ${proj.endDate} | ${proj.description}\n`;
  });

  text += `\nEducation:\n`;
  profile.education.forEach(edu => {
    text += `- ${edu.degree} in ${edu.field} from ${edu.school} | ${edu.startDate} - ${edu.endDate}\n`;
  });
  
  return text;
}

const handleStart = async (j: string, type: string) => {
  if (!isAuthenticated.value) {
    alert("Please log in first!");
    return;
  }

  // 检查额度
  if (Number(availableQuota.value) <= 0) {
    showPaymentModal.value = true;
    return;
  }
  isStarting.value = true;
  jd.value = j;
  interviewType.value = type; // 保存面试类型
  
  try {
    const saved = localStorage.getItem('userProfile');
    if (!saved) throw new Error("Profile not found");
    const profile: UserProfile = JSON.parse(saved);
    const profileText = formatProfileForAI(profile);
    
    loadingStep.value = 'Analyzing Profile vs Job Description...';
    const context = await analyzeResume(profileText, j); 
    
    resumeContext.value = context;
    loadingStep.value = 'Preparing Interviewer...';
    appState.value = 'interview';
    
  } catch (error) {
    console.error("Failed to initialize chat:", error);
    if (error.message === "QuotaExceeded") {
      showPaymentModal.value = true;
      availableQuota.value = 0;
    } else {
      alert("Failed to start the interview. Please check your backend connection.");
    }
  } finally {
    isStarting.value = false;
    loadingStep.value = '';
  }
};

const handleInterviewComplete = (history: { role: string; text: string }[]) => {
  const newRecord: InterviewRecord = {
    id: Math.random().toString(36).substring(2, 15),
    date: new Date().toISOString(),
    jobDescription: jd.value,
    type: interviewType.value,
    resumeContext: resumeContext.value,
    chatHistory: history,
  };
  
  const saved = localStorage.getItem('interviewHistory');
  const records = saved ? JSON.parse(saved) : [];
  records.push(newRecord);
  localStorage.setItem('interviewHistory', JSON.stringify(records));
  
  currentRecordId.value = newRecord.id;
  appState.value = 'feedback';
};

const handleViewHistory = (id: string) => {
  currentRecordId.value = id;
  appState.value = 'feedback';
};
const handleRestart = () => {
  appState.value = 'setup';
  interviewType.value = '';
  chatHistory.value = [];
  resumeContext.value = '';
  jd.value = '';
  currentRecordId.value = '';
};
</script>

<template>
  <div class="min-h-screen bg-gray-50 text-gray-900 font-sans">
    <div v-if="showPaymentModal" class="fixed inset-0 bg-gray-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div class="bg-white p-8 rounded-3xl max-w-md w-full shadow-2xl border border-gray-100 transform transition-all">
        <div class="text-center mb-6">
          <div class="w-16 h-16 bg-indigo-50 text-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4 rotate-3">
            <Bot class="w-8 h-8" />
          </div>
          <h2 class="text-2xl font-extrabold text-gray-900 mb-2">Unlock More Interviews</h2>
          <p class="text-gray-500 text-sm">Choose a package to continue your interview practice.</p>
        </div>
        
        <div class="grid grid-cols-2 gap-3 mb-6">
          <div 
            @click="selectedPackage = 1" 
            :class="['relative p-4 rounded-2xl border-2 cursor-pointer transition-all', selectedPackage === 1 ? 'border-indigo-600 bg-indigo-50' : 'border-gray-100 hover:border-gray-200 bg-white']"
          >
            <div v-if="selectedPackage === 1" class="absolute -top-2 -right-2 w-6 h-6 bg-indigo-600 text-white rounded-full flex items-center justify-center">
              <Check class="w-4 h-4" />
            </div>
            <h3 class="font-bold text-gray-900 text-sm">Single Run</h3>
            <p class="text-xs text-gray-500 mb-2">1 Mock Interview</p>
            <div class="text-2xl font-extrabold text-indigo-600">$1.99</div>
          </div>

          <div 
            @click="selectedPackage = 5" 
            :class="['relative p-4 rounded-2xl border-2 cursor-pointer transition-all', selectedPackage === 5 ? 'border-indigo-600 bg-indigo-50' : 'border-gray-100 hover:border-gray-200 bg-white']"
          >
            <div class="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-orange-400 to-red-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm whitespace-nowrap">
              Most Popular
            </div>
            <div v-if="selectedPackage === 5" class="absolute -top-2 -right-2 w-6 h-6 bg-indigo-600 text-white rounded-full flex items-center justify-center">
              <Check class="w-4 h-4" />
            </div>
            <h3 class="font-bold text-gray-900 text-sm">Pro Pack</h3>
            <p class="text-xs text-gray-500 mb-2">5 Mock Interviews</p>
            <div class="text-2xl font-extrabold text-indigo-600">$7.99</div>
            <div class="text-[10px] text-green-600 font-bold mt-1">Save ~20%</div>
          </div>
        </div>

        <div class="mb-8">
           <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Select Payment Method</p>
           <div class="flex space-x-3">
             <button 
               @click="selectedProvider = 'stripe'" 
               :class="['flex items-center justify-center flex-1 py-2.5 rounded-xl text-sm font-semibold transition-colors border', selectedProvider === 'stripe' ? 'bg-gray-900 text-white border-gray-900' : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50']"
             >
               <CreditCard class="w-4 h-4 mr-2" /> Stripe
             </button>
             <button 
               @click="selectedProvider = 'paypal'" 
               :class="['flex items-center justify-center flex-1 py-2.5 rounded-xl text-sm font-semibold transition-colors border', selectedProvider === 'paypal' ? 'bg-[#00457C] text-white border-[#00457C]' : 'bg-white text-gray-700 border-gray-200 hover:bg-gray-50']"
             >
               <svg class="w-4 h-4 mr-2 fill-current" viewBox="0 0 24 24"><path d="M7.076 21.337H2.47a.641.641 0 0 1-.633-.74L4.944.901C5.026.382 5.474 0 5.998 0h7.46c2.57 0 4.578.543 5.69 1.81 1.01 1.15 1.304 2.42 1.012 4.287-.023.143-.047.288-.077.437-.983 5.05-4.349 6.797-8.647 6.797h-.605a.64.64 0 0 0-.632.535l-.898 5.679a.639.639 0 0 1-.633.538h-1.6z"/></svg>
               PayPal
             </button>
           </div>
        </div>

        <div class="flex space-x-3">
          <button 
            @click="showPaymentModal = false" 
            class="w-1/3 px-4 py-3 bg-white border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button 
            @click="handlePay" 
            class="w-2/3 px-4 py-3 bg-indigo-600 text-white rounded-xl font-bold hover:bg-indigo-700 transition-colors shadow-md flex justify-center items-center"
          >
            Pay ${{ selectedPackage === 1 ? '1.99' : '7.99' }}
          </button>
        </div>
      </div>
    </div>

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
          <GoogleLogin 
            v-if="!isAuthenticated" 
            :callback="handleGoogleLoginSuccess" 
            prompt
          />
          <div v-else class="flex items-center space-x-6">
            <button @click="showPaymentModal = true" class="text-sm font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 transition-colors px-3 py-1.5 rounded-lg border border-indigo-100 flex items-center cursor-pointer">
              Quota: <span class="ml-1 text-indigo-900">{{ availableQuota }}</span>
              <span class="ml-2 text-xs bg-indigo-200 text-indigo-800 px-1.5 rounded">+</span>
            </button>
            <button 
              @click="appState = 'setup'"
              :class="['text-sm font-medium transition-colors', appState === 'setup' ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-900']"
            >
              Interview
            </button>
            <button 
              @click="appState = 'history'"
              :class="['flex items-center text-sm font-medium transition-colors', appState === 'history' ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-900']"
            >
              <Clock class="w-4 h-4 mr-1" />
              History
            </button>
            <button 
              @click="appState = 'profile'"
              :class="['flex items-center text-sm font-medium transition-colors', appState === 'profile' ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-900']"
            >
              <UserCircle class="w-4 h-4 mr-1" />
              My Profile
            </button>

            <button 
              @click="handleLogout"
              class="flex items-center text-sm font-medium text-gray-500 hover:text-red-600 transition-colors pl-4 border-l border-gray-200"
            >
              <LogOut class="w-4 h-4 mr-1" />
              Logout
            </button>
          </div>
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
        <HistoryList v-if="appState === 'history'" @view="handleViewHistory" />
        <InterviewChat 
          v-if="appState === 'interview'" 
          :resumeContext="resumeContext"
          :jobDescription="jd"
          :interviewType="interviewType"
          @complete="handleInterviewComplete" 
        />

        <FeedbackReport
          v-if="appState === 'feedback'"
          :recordId="currentRecordId"
          :chatHistory="chatHistory"
          :resume="resumeContext"
          :jobDescription="jd"
          @restart="handleRestart"
        />
     </main>
  </div>
</template>