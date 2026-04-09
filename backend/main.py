import os
import base64
import json
from io import BytesIO
from fastapi import FastAPI, HTTPException,Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
from gtts import gTTS
from google import genai
from google.genai import types
import jwt
import stripe
import requests
from motor.motor_asyncio import AsyncIOMotorClient
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET = os.getenv("JWT_SECRET")
DOMAIN_URL = os.getenv("DOMAIN_URL")
MONGODB_URL = os.getenv("MONGODB_URL")
# Stripe 配置
STRIPE_api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# PayPal 配置
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
PAYPAL_MODE = os.getenv("PAYPAL_MODE", "sandbox")
PAYPAL_BASE_URL = "https://api-m.paypal.com" if PAYPAL_MODE == "live" else "https://api-m.sandbox.paypal.com"

# --- MongoDB 初始化 ---
mongo_client = AsyncIOMotorClient(MONGODB_URL)
db = mongo_client.AI_interviewer
users_collection = db.users     
ip_logs_collection = db.ip_logs 

async def init_db_indexes():
    await users_collection.create_index("google_id", unique=True)
    await users_collection.create_index("email", unique=True)
    await ip_logs_collection.create_index("ip_address", unique=True)

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

# --- 辅助函数 ---
class GoogleAuthRequest(BaseModel):
    token: str

class PaymentRequest(BaseModel):
    provider: str  # "stripe" or "paypal"
    amount: int    # 1 或 5
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    try:
        print(JWT_SECRET)
        print(token)
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        google_id = payload.get("sub")
        user = await users_collection.find_one({"google_id": google_id})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_client_ip(request: Request):
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host

def get_paypal_access_token():
    auth = (PAYPAL_CLIENT_ID, PAYPAL_SECRET)
    headers = {"Accept": "application/json", "Accept-Language": "en_US"}
    data = {"grant_type": "client_credentials"}
    response = requests.post(f"{PAYPAL_BASE_URL}/v1/oauth2/token", auth=auth, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# ==========================================
# 鉴权 API
# ==========================================
@app.get("/api/user/quota")
async def get_user_quota(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户的最新面试额度"""
    # current_user 是从 MongoDB 查询返回的字典
    return {"quota": current_user.get("quota", 0)}
@app.post("/api/auth/google")
async def google_auth(req: GoogleAuthRequest, request: Request):
    try:
        idinfo = id_token.verify_oauth2_token(req.token, google_requests.Request(), GOOGLE_CLIENT_ID)
        google_id = idinfo['sub']
        email = idinfo['email']
        client_ip = get_client_ip(request)

        user = await users_collection.find_one({"google_id": google_id})
        is_new_user = False
        
        if not user:
            user = {"google_id": google_id, "email": email, "quota": 0}
            await users_collection.insert_one(user)
            is_new_user = True

        ip_log = await ip_logs_collection.find_one({"ip_address": client_ip})
        
        if is_new_user:
            if not ip_log or not ip_log.get("used_free_tier", False):
                await users_collection.update_one({"google_id": google_id}, {"$inc": {"quota": 1}})
                user["quota"] += 1
                
                if not ip_log:
                    await ip_logs_collection.insert_one({"ip_address": client_ip, "used_free_tier": True})
                else:
                    await ip_logs_collection.update_one({"ip_address": client_ip}, {"$set": {"used_free_tier": True}})

        access_token = jwt.encode({"sub": user["google_id"]}, JWT_SECRET, algorithm="HS256")
        return {"token": access_token, "quota": user["quota"]}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")


# ==========================================
# 支付 API (Stripe & PayPal)
# ==========================================

@app.post("/api/create-checkout-session")
async def create_checkout_session(req: PaymentRequest, current_user: dict = Depends(get_current_user)):
    try:
        # 确定套餐价格与名称
        if req.amount == 1:
            price_cents = 199
            price_dollars = "1.99"
            name = "Single Run (1 Mock Interview)"
        elif req.amount == 5:
            price_cents = 799
            price_dollars = "7.99"
            name = "Pro Pack (5 Mock Interviews)"
        else:
            raise HTTPException(status_code=400, detail="Invalid package amount")

        # 处理 Stripe 支付
        if req.provider == 'stripe':
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {'name': name},
                        'unit_amount': price_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=DOMAIN_URL + '?payment=success',
                cancel_url=DOMAIN_URL + '?payment=cancel',
                client_reference_id=current_user["google_id"],
                metadata={"quota_amount": req.amount}  # Webhook 回调时读取此值
            )
            return {"url": session.url}

        # 处理 PayPal 支付
        elif req.provider == 'paypal':
            access_token = get_paypal_access_token()
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}"
            }
            # 利用 custom_id 透传用户和购买额度信息 (格式: google_id|quota_amount)
            custom_id = f"{current_user['google_id']}|{req.amount}"
            
            order_payload = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": f"mock_interview_{req.amount}",
                    "custom_id": custom_id,
                    "description": name,
                    "amount": {
                        "currency_code": "USD",
                        "value": price_dollars
                    }
                }],
                "application_context": {
                    "return_url": DOMAIN_URL + "?payment=success",
                    "cancel_url": DOMAIN_URL + "?payment=cancel",
                    "user_action": "PAY_NOW"
                }
            }
            res = requests.post(f"{PAYPAL_BASE_URL}/v2/checkout/orders", headers=headers, json=order_payload)
            res.raise_for_status()
            
            # 返回 PayPal 的授权跳转链接
            approve_url = next(link["href"] for link in res.json()["links"] if link["rel"] == "approve")
            return {"url": approve_url}
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported payment provider")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        google_id = session.get('client_reference_id')
        metadata = session.get('metadata', {})
        quota_to_add = int(metadata.get('quota_amount', 0))
        
        if google_id and quota_to_add > 0:
            await users_collection.update_one(
                {"google_id": google_id}, 
                {"$inc": {"quota": quota_to_add}}
            )
    return {"status": "success"}


@app.post("/api/webhook/paypal")
async def paypal_webhook(request: Request):
    event = await request.json()
    
    # 监听用户已在 PayPal 端同意付款的事件，后端主动触发扣款(Capture)
    if event.get("event_type") == "CHECKOUT.ORDER.APPROVED":
        resource = event.get("resource", {})
        order_id = resource.get("id")
        
        access_token = get_paypal_access_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}"
        }
        # 主动调用 Capture 捕获这笔资金
        capture_res = requests.post(f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture", headers=headers)
        
        if capture_res.status_code in (200, 201):
            purchase_units = resource.get("purchase_units", [])
            if purchase_units:
                # 解析我们在生成订单时塞进去的 custom_id
                custom_id = purchase_units[0].get("custom_id", "")
                if "|" in custom_id:
                    try:
                        google_id, quota_str = custom_id.split("|")
                        quota_to_add = int(quota_str)
                        await users_collection.update_one(
                            {"google_id": google_id}, 
                            {"$inc": {"quota": quota_to_add}}
                        )
                    except Exception as e:
                        print(f"PayPal Custom ID Parse Error: {e}")

    return {"status": "success"}

'''
# ==========================================
# 核心功能 API
# ==========================================
# '''
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
async def analyze_resume(request: AnalyzeResumeRequest, current_user: dict = Depends(get_current_user)):
    """Compare the candidate's profile against the job description and identify key matches and gaps"""
    
    if current_user.get("quota", 0) <= 0:
        raise HTTPException(status_code=403, detail="Not enough quota. Please purchase more.")
    
    await users_collection.update_one(
        {"google_id": current_user["google_id"]}, 
        {"$inc": {"quota": -1}}
    )
    
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