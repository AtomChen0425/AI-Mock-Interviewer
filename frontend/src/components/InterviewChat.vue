<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';
import { Send, Loader2, CheckCircle, Bot, User, Mic, MicOff, Eye, EyeOff, Volume2 } from 'lucide-vue-next';

import { generateSpeech, sendInterviewMessage } from '../services/apiService';

const props = defineProps<{
  resumeContext: string;
  jobDescription: string;
  interviewType: string;
}>();

const emit = defineEmits<{
  (e: 'complete', history: { role: string; text: string }[]): void;
}>();

interface Message {
  role: 'user' | 'model';
  text: string;
  hidden?: boolean; 
}

const messages = ref<Message[]>([]);
const input = ref('');
const isLoading = ref(true);
const isRecording = ref(false);
const showTranscript = ref(false);
const isPlayingAudio = ref(false);

const messagesEndRef = ref<HTMLDivElement | null>(null);
const recognitionRef = ref<any>(null);
const audioContextRef = ref<AudioContext | null>(null);
const currentAudioSourceRef = ref<AudioBufferSourceNode | null>(null);

// ⚠️ 修改点 4：计算属性，仅用于在 UI 上展示不隐藏的消息
const visibleMessages = computed(() => messages.value.filter(m => !m.hidden));

const scrollToBottom = () => {
  nextTick(() => {
    messagesEndRef.value?.scrollIntoView({ behavior: 'smooth' });
  });
};

watch(messages, scrollToBottom, { deep: true });

// const stopAudio = () => {
//   if (currentAudioSourceRef.value) {
//     currentAudioSourceRef.value.stop();
//     currentAudioSourceRef.value.disconnect();
//     currentAudioSourceRef.value = null;
//   }
//   isPlayingAudio.value = false;
// };

// const playAudio = async (text: string) => {
//   stopAudio();
//   isPlayingAudio.value = true;
//   try {
//     const audioBase64 = await generateSpeech(text);
//     if (!audioBase64) {
//       isPlayingAudio.value = false;
//       return;
//     }
//     const binaryString = window.atob(audioBase64);
//     const len = binaryString.length;
//     const bytes = new Uint8Array(len);
//     for (let i = 0; i < len; i++) {
//       bytes[i] = binaryString.charCodeAt(i);
//     }
//     if (!audioContextRef.value) {
//       audioContextRef.value = new (window.AudioContext || (window as any).webkitAudioContext)();
//     }
//     const audioBuffer = await audioContextRef.value.decodeAudioData(bytes.buffer);
//     const source = audioContextRef.value.createBufferSource();
//     source.buffer = audioBuffer;
//     source.connect(audioContextRef.value.destination);
//     source.onended = () => {
//       isPlayingAudio.value = false;
//     };
//     currentAudioSourceRef.value = source;
//     source.start(0);
//   } catch (error) {
//     console.error("Failed to play audio:", error);
//     isPlayingAudio.value = false;
//   }
// };
const playAudio = (text: string) => {
  isPlayingAudio.value = true;
  
  window.speechSynthesis.cancel(); 
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-US'; 
  
  utterance.rate = 0.9; 
  utterance.pitch = 1.0; 

  utterance.onend = () => {
    isPlayingAudio.value = false;
  };

  utterance.onerror = (event) => {
    console.error("Speech synthesis error", event);
    isPlayingAudio.value = false;
  };

  window.speechSynthesis.speak(utterance);
};

const stopAudio = () => {
  window.speechSynthesis.cancel();
  isPlayingAudio.value = false;
};

const getApiHistory = () => {
  return messages.value.map(m => ({
    role: m.role,
    parts: [m.text]
  }));
};

const startInterview = async () => {
  try {
    const initMessage = "Hello, I am ready to start the interview.";
    
    const responseText = await sendInterviewMessage(
      props.resumeContext,
      props.jobDescription,
      props.interviewType,
      initMessage,
      []
    );

    messages.value.push({ role: 'user', text: initMessage, hidden: true });
    messages.value.push({ role: 'model', text: responseText });
    
    playAudio(responseText);
  } catch (error) {
    console.error("Failed to get initial message:", error);
    messages.value.push({ role: 'model', text: "Hello! Let's start the interview. Can you introduce yourself?" });
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  startInterview();

  // ... [此处保留原有语音识别 SpeechRecognition 的初始化代码] ...
  const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
  if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      input.value = transcript;
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error', event.error);
      isRecording.value = false;
    };

    recognition.onend = () => {
      isRecording.value = false;
    };

    recognitionRef.value = recognition;
  }
});

onUnmounted(() => {
  stopAudio();
  if (audioContextRef.value) {
    audioContextRef.value.close();
  }
});

const toggleRecording = () => {
  if (isRecording.value) {
    recognitionRef.value?.stop();
    isRecording.value = false;
  } else {
    input.value = '';
    recognitionRef.value?.start();
    isRecording.value = true;
  }
};

const handleSubmit = async (e?: Event) => {
  e?.preventDefault();
  if (!input.value.trim() || isLoading.value) return;

  stopAudio();

  const userMessage = input.value;
  // 获取加上新消息前的历史记录
  const currentHistory = getApiHistory(); 

  messages.value.push({ role: 'user', text: userMessage });
  input.value = '';
  isLoading.value = true;

  try {
    // ⚠️ 修改点 6：调用后端接口
    const responseText = await sendInterviewMessage(
      props.resumeContext,
      props.jobDescription,
      props.interviewType,
      userMessage,
      currentHistory
    );
    
    messages.value.push({ role: 'model', text: responseText });
    playAudio(responseText);
  } catch (error) {
    console.error("Failed to send message:", error);
    messages.value.push({ role: 'model', text: "I'm sorry, I encountered an error. Could you repeat that?" });
  } finally {
    isLoading.value = false;
  }
};

const handleComplete = async () => {
  stopAudio();
  isLoading.value = true;
  try {
    const finishMessage = "I would like to finish the interview now. Please provide your final feedback.";
    const currentHistory = getApiHistory();

    // 同样，将结束指令标记为 hidden
    messages.value.push({ role: 'user', text: finishMessage, hidden: true });

    // ⚠️ 修改点 7：调用后端接口
    const responseText = await sendInterviewMessage(
      props.resumeContext,
      props.jobDescription,
      props.interviewType,
      finishMessage,
      currentHistory
    );
    
    messages.value.push({ role: 'model', text: responseText });
    await playAudio(responseText);
    
    setTimeout(() => {
      // 传递完整的 messages（包括 hidden），方便 FeedbackReport 全面评估
      emit('complete', messages.value);
    }, 2000);
  } catch (error) {
    emit('complete', messages.value);
  }
};
</script>

<template>
  <div class="max-w-4xl mx-auto bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col h-[800px]">
    <div class="bg-indigo-600 p-4 text-white flex justify-between items-center shrink-0">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center relative">
          <Bot class="w-6 h-6" />
          <span v-if="isPlayingAudio" class="absolute -top-1 -right-1 flex h-3 w-3">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </span>
        </div>
        <div>
          <h2 class="font-semibold text-lg">AI Interviewer</h2>
          <p class="text-indigo-100 text-sm flex items-center">
            <span v-if="isPlayingAudio" class="flex items-center">
              <Volume2 class="w-3 h-3 mr-1 animate-pulse" /> Speaking...
            </span>
            <span v-else>Active Session</span>
          </p>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <button
          @click="showTranscript = !showTranscript"
          class="flex items-center px-3 py-1.5 bg-white/10 hover:bg-white/20 rounded-lg text-sm font-medium transition-colors"
          :title="showTranscript ? 'Hide text to practice listening' : 'Show text'"
        >
          <EyeOff v-if="showTranscript" class="w-4 h-4 mr-2" />
          <Eye v-else class="w-4 h-4 mr-2" />
          {{ showTranscript ? 'Hide Text' : 'Show Text' }}
        </button>
        <button
          @click="handleComplete"
          :disabled="isLoading"
          class="flex items-center px-4 py-2 bg-white text-indigo-600 rounded-lg text-sm font-bold hover:bg-indigo-50 transition-colors disabled:opacity-50"
        >
          <CheckCircle class="w-4 h-4 mr-2" />
          Finish & Get Feedback
        </button>
      </div>
      </div>

    <div class="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50">
      <div
        v-for="(msg, index) in visibleMessages"
        :key="index"
        :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']"
      >
        <div :class="['flex max-w-[80%]', msg.role === 'user' ? 'flex-row-reverse' : 'flex-row']">
          <div :class="['w-8 h-8 rounded-full flex items-center justify-center shrink-0', msg.role === 'user' ? 'bg-indigo-100 text-indigo-600 ml-3' : 'bg-gray-200 text-gray-600 mr-3']">
            <User v-if="msg.role === 'user'" class="w-5 h-5" />
            <Bot v-else class="w-5 h-5" />
          </div>
          <div
            :class="[
              'p-4 rounded-2xl text-sm leading-relaxed group',
              msg.role === 'user' 
                ? 'bg-indigo-600 text-white rounded-tr-none' 
                : 'bg-white border border-gray-200 text-gray-800 rounded-tl-none shadow-sm',
              !showTranscript && msg.role === 'model' ? 'blur-sm hover:blur-none transition-all duration-300 select-none' : ''
            ]"
          >
            {{ msg.text }}
            <div v-if="!showTranscript && msg.role === 'model'" class="text-[10px] text-gray-400 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
              (Hover to reveal text)
            </div>
          </div>
        </div>
      </div>
      
      <div ref="messagesEndRef"></div>
    </div>

    <div class="p-4 bg-white border-t border-gray-200 shrink-0">
      <form @submit.prevent="handleSubmit" class="flex items-end space-x-3">
        <div class="flex-1 relative">
          <textarea
            v-model="input"
            @keydown.enter.prevent="handleSubmit"
            rows="2"
            class="w-full px-4 py-3 pr-12 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none bg-gray-50/50 text-sm"
            placeholder="Type your answer or use voice input..."
            :disabled="isLoading"
          ></textarea>
          <button
            type="button"
            @click="toggleRecording"
            :disabled="isLoading || !recognitionRef"
            :class="[
              'absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-full transition-colors',
              isRecording ? 'bg-red-100 text-red-600 animate-pulse' : 'text-gray-400 hover:text-indigo-600 hover:bg-gray-100'
            ]"
            :title="recognitionRef ? 'Voice Input' : 'Voice input not supported in this browser'"
          >
            <MicOff v-if="isRecording" class="w-5 h-5" />
            <Mic v-else class="w-5 h-5" />
          </button>
        </div>
        <button
          type="submit"
          :disabled="!input.trim() || isLoading"
          class="self-center p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm "
        >
          <Loader2 v-if="isLoading" class="w-5 h-5 animate-spin" />
          <Send v-else class="w-5 h-5" />
        </button>
      </form>
      </div>
  </div>
</template>