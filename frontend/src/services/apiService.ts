import type { UserProfile } from "../types";

const API_BASE_URL = 'http://localhost:8000/api';

// ---------------------------------------------------------------------------
// 1. 语音生成 (Text-to-Speech)
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
    
    // ⚠️ 修改这里：解析 JSON 并获取 audio 属性
    if (response.ok) {
        const data = await response.json();
        return data.audio; // 拿到纯净的 Base64 字符串
    }
    return null;
  } catch (e) {
    console.error("TTS error:", e);
    return null;
  }
}

// ---------------------------------------------------------------------------
// 2. 解析简历文件为结构化数据 (Profile)
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
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    // 假设 FastAPI 直接返回纯文本结果。如果是 JSON {"result": "..."}, 请改为 await response.json()
    return await response.text(); 
  } catch (e) {
    console.error("Resume analysis failed:", e);
    return "Resume analysis failed. Please check backend connection.";
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