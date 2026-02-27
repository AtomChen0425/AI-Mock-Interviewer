import base64
import json
from io import BytesIO
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from gtts import gTTS
from google import genai
from google.genai import types

load_dotenv()
gemini_model = "gemini-2.5-flash"  # or "gemini-2.5-pro" for more advanced capabilities
client = genai.Client() 

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TTSRequest(BaseModel):
    message: str

class ParseResumeRequest(BaseModel):
    message: str
    mimeType: str

class AnalyzeResumeRequest(BaseModel):
    profileText: str
    jobDescription: str

class ChatMessagePart(BaseModel):
    role: str
    parts: List[str]

class ChatRequest(BaseModel):
    resume: str
    jobDescription: str
    interviewType: str
    message: str
    history: List[ChatMessagePart] = []

class FeedbackHistoryItem(BaseModel):
    role: str
    text: str

class FeedbackRequest(BaseModel):
    resume: str
    jobDescription: str
    chatHistory: List[FeedbackHistoryItem]

@app.post("/api/tts")
def text_to_speech(request: TTSRequest):
    try:
        tts = gTTS(text=request.message, lang='en')
        fp = BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_base64 = base64.b64encode(fp.read()).decode('utf-8')
        return {"audio": audio_base64} 
        
    except Exception as e:
        print(f"TTS Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate speech")


@app.post("/api/parse-resume")
async def parse_resume(request: ParseResumeRequest):
    """parse the resume text and extract structured information about the candidate's profile, including their name, contact details, skills, work experience, project experience, and education history. The response should be a well-structured JSON object that can be easily consumed by the frontend for display and further analysis."""
    prompt = """
    You are an expert technical recruiter. Parse the attached resume and extract the information into a structured JSON format.
    Extract the candidate's name, email, phone, a brief professional summary, a comma-separated list of skills, their work experience, project experience, and education.
    For work experience, include title, company, location, startDate, endDate, type (e.g., Full-time, Internship), and a detailed description (bullet points preferred).
    For project experience, include title, startDate, endDate, and description.
    For education, include school, degree, field of study, startDate, and endDate.
    Extract the following information from the provided resume text and return it as a structured JSON object. 
    Use exactly this schema:
    {
      "name": "string",
      "email": "string",
      "phone": "string",
      "summary": "string",
      "skills": "string (comma separated)",
      "workexperience": [
        {"title": "string", "company": "string", "location": "string", "startDate": "string", "endDate": "string", "type": "string", "description": "string"}
      ],
      "projectexperience": [
        {"title": "string", "startDate": "string", "endDate": "string", "description": "string"}
      ],
      "education": [
        {"degree": "string", "field": "string", "school": "string", "startDate": "string", "endDate": "string"}
      ]
    }
    
    Resume Text:
    """ 

    try:
        file_bytes = base64.b64decode(request.message)
        
        document_part = types.Part.from_bytes(
            data=file_bytes,
            mime_type=request.mimeType,
        )

        response = await client.aio.models.generate_content(
            model=gemini_model,
            contents=[document_part, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        # print(f"Raw response from model: {response.text}")  # Debug log to see the raw response
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze-resume")
async def analyze_resume(request: AnalyzeResumeRequest):
    """Compare the candidate's profile against the job description and identify key matches and gaps"""
    prompt = f"""
    Analyze the candidate's profile against the job description.
    Highlight key matches, missing skills, and potential areas to probe during the interview.
    Keep it concise and objective.
    
    Candidate Profile:
    {request.profileText}
    
    Job Description:
    {request.jobDescription}
    """
    try:
        response = await client.aio.models.generate_content(
            model=gemini_model,
            contents=prompt
        )
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def interview_chat(request: ChatRequest):
    """Proceed with the mock interview conversation, maintaining context and following the specified instructions"""
    system_instruction = f"""You are an expert technical and behavioral interviewer conducting a mock interview for a candidate.
    
    Context:
    - Candidate's Resume Analysis: 
    {request.resume}
    
    - Job Description: 
    {request.jobDescription}
    
    - Interview Type: {request.interviewType}
    
    Instructions:
    1. Start by introducing yourself briefly and asking the first question based on the candidate's background and the job description.
    2. Ask ONE question at a time. Wait for the candidate's response before asking the next question.
    3. Your questions should be highly personalized based on the Resume Analysis provided above. Focus on their specific skills and how they align (or don't align) with the JD.
    4. If the candidate's answer is incomplete or unclear, ask follow-up questions to dig deeper.
    5. Maintain a professional, encouraging, yet rigorous tone.
    6. Do NOT provide feedback or evaluate the candidate's answers during the interview. Save all feedback for the end.
    7. Keep the interview to about 4-5 main questions.
    8. When you feel the interview is complete, or if the candidate asks to finish, say exactly: "INTERVIEW_COMPLETE".`;

    """

    try:
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
        )
        
        formatted_history = []
        for item in request.history:
            parts = [types.Part.from_text(text=text) for text in item.parts]
            content = types.Content(role=item.role, parts=parts)
            formatted_history.append(content)
        
        chat = client.aio.chats.create(
            model=gemini_model,
            config=config,
            history=formatted_history
        )

        response = await chat.send_message(request.message)
        
        return {"reply": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-feedback")
async def generate_feedback(request: FeedbackRequest):
    """Finally, after the interview is complete, generate a comprehensive feedback report based on the entire interview transcript, the candidate's resume, and the job description. Provide specific feedback on their answers, communication skills, and overall fit for the role."""
    chat_transcript = "\n".join(
        [f"{'Candidate' if item.role == 'user' else 'Interviewer'}: {item.text}" 
         for item in request.chatHistory]
    )

    prompt = f"""
    You are an expert technical recruiter and senior engineer. Review the following interview transcript and provide comprehensive feedback.
    
    Job Description Context:
    {request.jobDescription}
    
    Resume Context:
    {request.resume}
    
    Interview Transcript:
    {chat_transcript}
    
    Please provide a comprehensive evaluation and feedback report for the candidate. Format your response in Markdown.
    Include the following sections:
    1. **Overall Score**: Give a score out of 100 and a brief summary of their performance.
    2. **Strengths**: Highlight what the candidate did well.
    3. **Areas for Improvement**: Point out specific areas where the candidate struggled or could improve.
    4. **Detailed Answer Feedback**: Review each of the candidate's main answers. Provide specific feedback on what was good and how they could have structured or answered it better (e.g., using the STAR method).
    5. **Communication & Grammar**: Evaluate the candidate's language proficiency, grammar, vocabulary, and clarity of expression. Provide specific corrections for any awkward phrasing, grammatical errors, or unclear expressions made during the interview.
    6. **Final Recommendation**: Would you proceed with this candidate to the next round? Why or why not?
    """
    
    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.5-pro',
            contents=prompt
        )
        return {"feedback": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))