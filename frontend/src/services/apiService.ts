import type { UserProfile } from "../types";

const API_BASE_URL = 'http://localhost:8000/api';

// ---------------------------------------------------------------------------
// 0. 鉴权与通用请求封装
// ---------------------------------------------------------------------------

// 获取本地存储的 JWT Token
export const getToken = () => localStorage.getItem('authToken');

// 封装带有 Authorization 请求头的 fetch
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  const token = getToken();
  
  // 合并 headers
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return fetch(url, { ...options, headers });
}

// ---------------------------------------------------------------------------
// 1. Google 登录与支付管理
// ---------------------------------------------------------------------------

// 验证 Google Token 并换取后端 JWT Token 与剩余额度
export async function loginWithGoogle(credential: string): Promise<{token: string, quota: number} | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: credential })
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('authToken', data.token); // 保存 Token 到本地
      return data;
    }
    return null;
  } catch (error) {
    console.error("Google login error:", error);
    return null;
  }
}

// 查询当前用户的最新 Quota
export async function getUserQuota(): Promise<number | null> {
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/user/quota`, {
      method: 'GET'
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.quota;
    }
    return null; // 如果返回 401，说明 Token 过期或无效
  } catch (error) {
    console.error("Failed to fetch quota:", error);
    return null;
  }
}

// 清除本地 Token
export function logoutUser() {
  localStorage.removeItem('authToken');
}
// 获取 支付链接
export async function getPaymentUrl(provider: 'stripe' | 'paypal', amount: number): Promise<string | null> {
  try {
    const response = await fetchWithAuth(`${API_BASE_URL}/create-checkout-session`, { 
      method: 'POST',
      body: JSON.stringify({ 
        provider: provider, 
        amount: amount 
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.url;
    }
    return null;
  } catch (error) {
    console.error("Payment URL error:", error);
    return null;
  }
}
// ---------------------------------------------------------------------------
// 1. (Text-to-Speech)
// ---------------------------------------------------------------------------
export async function generateSpeech(text: string): Promise<string | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/tts`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            message: text
        }),
    });
    

    if (response.ok) {
        const data = await response.json();
        return data.audio; 
    }
    return null;
  } catch (e) {
    console.error("TTS error:", e);
    return null;
  }
}

// ---------------------------------------------------------------------------
// 2.  (Profile)
// ---------------------------------------------------------------------------
export async function parseResumeToProfile(fileData: string, mimeType: string): Promise<UserProfile | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/parse-resume`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        message: fileData,
        mimeType: mimeType
      }),
    });
    
    if (response.ok) {
      const data = await response.json();
      // 补充缺失的 id 字段
      data.experience = data.experience?.map((e: any) => ({ ...e, id: e.id || Math.random().toString(36).substring(2, 9) })) || [];
      data.education = data.education?.map((e: any) => ({ ...e, id: e.id || Math.random().toString(36).substring(2, 9) })) || [];
      return data as UserProfile;
    } else {
      console.error("Backend failed to parse resume:", await response.text());
      return null;
    }
  } catch (e) {
    console.error("Failed to parse resume (Network Error):", e);
    return null;
  }
}

// ---------------------------------------------------------------------------
// 3. 将简历与 JD 对比，生成面试官上下文
// ---------------------------------------------------------------------------
export async function analyzeResume(profileText: string, jobDescription: string): Promise<string> {
  try {
    // ⚠️ 修正：改用专属的路由名称
    const response = await fetch(`${API_BASE_URL}/analyze-resume`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        profileText: profileText,
        jobDescription: jobDescription
      }),
    });
  
    if (!response.ok) {
      // 如果后端返回 403 错误（代表额度不足），抛出专属异常让 App.vue 弹窗处理
      if (response.status === 403) {
        throw new Error("QuotaExceeded");
      }
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.text(); 
  } catch (e) {
    console.error("Resume analysis failed:", e);
    throw e; // 抛出让前端捕获
  }
}

// ---------------------------------------------------------------------------
// 4. 面试聊天交互
// ---------------------------------------------------------------------------
export interface ChatMessage {
  role: 'user' | 'model';
  parts: string[]; 
}

export async function sendInterviewMessage(
  resume: string,
  jobDescription: string,
  interviewType: string,
  message: string,
  history: ChatMessage[]
): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        resume,
        jobDescription,
        interviewType,
        message,
        history
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend chat API returned status ${response.status}`);
    }

    const data = await response.json();
    return data.reply; // 依赖后端返回 {"reply": "..."} 格式
  } catch (error) {
    console.error("Failed to fetch response from backend:", error);
    throw error; // 继续向上抛出，让 InterviewChat.vue 捕获并显示友好提示
  }
}

// ---------------------------------------------------------------------------
// 5. 生成最终的面试反馈报告
// ---------------------------------------------------------------------------
export async function generateFeedback(
  chatHistory: { role: string; text: string }[], 
  resume: string, 
  jobDescription: string
): Promise<string> {
  try {
    const response = await fetch(`${API_BASE_URL}/generate-feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        resume,
        jobDescription,
        chatHistory,
      }),
    });

    if (!response.ok) {
      // ⚠️ 修正：复制粘贴的错误提示已修复
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data.feedback;
  } catch (error) {
    console.error("Failed to generate feedback:", error);
    return "Feedback generation failed. Please try again later.";
  }
}