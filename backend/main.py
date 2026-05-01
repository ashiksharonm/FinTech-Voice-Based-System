import os
import base64
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
from groq import Groq
import edge_tts

from . import database, agent
from .database import engine, SessionLocal, ChatSession, Message

# Initialize database
database.init_db()

app = FastAPI(title="FinBot-Analytics API")

# Initialize standard Groq client for Audio (Whisper)
groq_api_key = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=groq_api_key) if groq_api_key else None

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    session_id: str = None
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str

class VoiceChatResponse(BaseModel):
    session_id: str
    user_message: str
    response: str
    audio_base64: Optional[str] = None

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: DBSession = Depends(get_db)):
    session_id = request.session_id
    
    if not session_id:
        session_id = str(uuid.uuid4())
        new_session = ChatSession(session_id=session_id)
        db.add(new_session)
        db.commit()
    else:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            new_session = ChatSession(session_id=session_id)
            db.add(new_session)
            db.commit()

    user_msg = Message(
        session_id=session_id,
        role="user",
        content=request.message
    )
    db.add(user_msg)
    db.commit()

    history_records = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp).all()
    history = [{"role": msg.role, "content": msg.content} for msg in history_records][:-1]

    try:
        bot_response = agent.generate_response(request.message, history)
        
        bot_msg = Message(
            session_id=session_id,
            role="assistant",
            content=bot_response.response_text,
            intent=bot_response.detected_intent,
            sentiment_score=bot_response.user_sentiment
        )
        db.add(bot_msg)
        
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if bot_response.recommended_product:
            session.final_intent = bot_response.recommended_product
            session.status = "completed"
            
        db.commit()
        
        return ChatResponse(session_id=session_id, response=bot_response.response_text)
        
    except Exception as e:
        print(f"Error generating response: {e}")
        fallback_msg = "I'm sorry, I encountered an error processing your request. Could you please rephrase?"
        bot_msg = Message(
            session_id=session_id,
            role="assistant",
            content=fallback_msg
        )
        db.add(bot_msg)
        db.commit()
        return ChatResponse(session_id=session_id, response=fallback_msg)


@app.post("/chat/voice", response_model=VoiceChatResponse)
async def chat_voice_endpoint(
    audio_file: UploadFile = File(...),
    session_id: str = Form(None),
    db: DBSession = Depends(get_db)
):
    if not groq_client:
        raise HTTPException(status_code=500, detail="Groq API key not configured for audio transcription.")
        
    # 1. Save uploaded file temporarily to pass to Whisper
    temp_audio_path = f"/tmp/{uuid.uuid4()}_{audio_file.filename}"
    with open(temp_audio_path, "wb") as buffer:
        buffer.write(await audio_file.read())
        
    # 2. Transcribe Audio (ASR)
    try:
        with open(temp_audio_path, "rb") as audio_file_obj:
            transcription = groq_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=("audio.wav", audio_file_obj.read())
            )
        user_message_text = transcription.text
    except Exception as e:
        os.remove(temp_audio_path)
        raise HTTPException(status_code=500, detail=f"ASR failed: {str(e)}")
        
    os.remove(temp_audio_path)
    
    if not session_id:
        session_id = str(uuid.uuid4())
        new_session = ChatSession(session_id=session_id)
        db.add(new_session)
        db.commit()
    else:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if not session:
            new_session = ChatSession(session_id=session_id)
            db.add(new_session)
            db.commit()

    user_msg = Message(session_id=session_id, role="user", content=user_message_text)
    db.add(user_msg)
    db.commit()

    history_records = db.query(Message).filter(Message.session_id == session_id).order_by(Message.timestamp).all()
    history = [{"role": msg.role, "content": msg.content} for msg in history_records][:-1]

    try:
        bot_response = agent.generate_response(user_message_text, history)
        
        bot_msg = Message(
            session_id=session_id,
            role="assistant",
            content=bot_response.response_text,
            intent=bot_response.detected_intent,
            sentiment_score=bot_response.user_sentiment
        )
        db.add(bot_msg)
        
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if bot_response.recommended_product:
            session.final_intent = bot_response.recommended_product
            session.status = "completed"
            
        db.commit()
        
        # 3. Text to Speech (TTS) using edge-tts
        temp_tts_path = f"/tmp/{uuid.uuid4()}_tts.mp3"
        communicate = edge_tts.Communicate(bot_response.response_text, "en-US-AriaNeural")
        await communicate.save(temp_tts_path)
        
        # Read the generated TTS file and encode directly to base64
        with open(temp_tts_path, "rb") as tts_file:
            audio_base64 = base64.b64encode(tts_file.read()).decode("utf-8")
        
        os.remove(temp_tts_path)
        
        return VoiceChatResponse(
            session_id=session_id, 
            user_message=user_message_text,
            response=bot_response.response_text,
            audio_base64=audio_base64
        )
        
    except Exception as e:
        print(f"Error in voice endpoint: {e}")
        fallback_msg = "I'm sorry, I encountered an error processing your request."
        bot_msg = Message(session_id=session_id, role="assistant", content=fallback_msg)
        db.add(bot_msg)
        db.commit()
        return VoiceChatResponse(session_id=session_id, user_message=user_message_text if 'user_message_text' in locals() else "", response=fallback_msg)

@app.get("/analytics")
def get_analytics(db: DBSession = Depends(get_db)):
    total_sessions = db.query(ChatSession).count()
    completed_sessions = db.query(ChatSession).filter(ChatSession.status == "completed").count()
    
    drop_off_rate = 0
    if total_sessions > 0:
        drop_off_rate = ((total_sessions - completed_sessions) / total_sessions) * 100
        
    intents = db.query(Message.intent).filter(Message.intent != None).all()
    intent_counts = {}
    for i in intents:
        intent = i[0]
        intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
    sentiments = db.query(Message.sentiment_score).filter(Message.sentiment_score != None).all()
    avg_sentiment = 0
    if sentiments:
        avg_sentiment = sum(s[0] for s in sentiments) / len(sentiments)
        
    final_intents = db.query(ChatSession.final_intent).filter(ChatSession.final_intent != None).all()
    product_counts = {}
    for i in final_intents:
        product = i[0]
        product_counts[product] = product_counts.get(product, 0) + 1

    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "drop_off_rate": round(drop_off_rate, 2),
        "intent_distribution": intent_counts,
        "average_sentiment": round(avg_sentiment, 2),
        "product_recommendations": product_counts
    }
