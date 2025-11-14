from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import base64
import numpy as np
import cv2
import wave
import os
import sys
from datetime import datetime

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
os.chdir(current_dir)

print(f"Working directory: {os.getcwd()}")

# Import emotion analysis modules FIRST
print("Loading emotion analysis modules...")
try:
    from emotion_analysis.emotion_analyzer import EmotionAnalyzer
    from emotion_analysis.voice_analyzer import VoiceAnalyzer
    from emotion_analysis.face_detector import FaceDetector
    from emotion_analysis.multimodal_integration import MultimodalAnalyzer
    from emotion_analysis.document_analyzer import DocumentAnalyzer
    from intent_classification.intent_classifier import IntentClassifier
    print("✓ Emotion analysis modules imported successfully")
except ImportError as e:
    print(f"✗ Emotion Analysis Import Error: {e}")
    sys.exit(1)

# Import database and auth modules SECOND
print("Loading database and auth modules...")
try:
    from database.config import connect_to_mongo, close_mongo_connection, get_database
    from database.crud import save_message
    from routes.auth_routes import router as auth_router
    from routes.session_routes import router as session_router
    from routes.appointment_routes import router as appointment_router
    from routes.admin_routes import router as admin_router
    from auth.auth_handler import get_current_user
    print("✓ Database and auth modules imported successfully")
    DB_ENABLED = True
except ImportError as e:
    print(f"✗ Database Import Error: {e}")
    print("Continuing without database features...")
    from fastapi import APIRouter
    auth_router = APIRouter()
    session_router = APIRouter()
    appointment_router = APIRouter()
    admin_router = APIRouter()
    DB_ENABLED = False
    get_database = lambda: None
    save_message = None

app = FastAPI(title="Mental Health AI Assistant API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection events
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()
    print("✓ Application startup complete")

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()
    print("✓ Application shutdown complete")

# Include routers
app.include_router(auth_router)
app.include_router(session_router)
app.include_router(appointment_router)
app.include_router(admin_router)

# Initialize analyzers
print("Loading AI models...")
emotion_analyzer = EmotionAnalyzer("models/my_model.h5")
voice_analyzer = VoiceAnalyzer()
face_detector = FaceDetector()
intent_classifier = IntentClassifier(model_dir="intent_classification/intent_models")
multimodal_analyzer = MultimodalAnalyzer(emotion_analyzer, intent_classifier, voice_analyzer)
document_analyzer = DocumentAnalyzer()
print("✓ Models loaded successfully!")

# Store active sessions
active_sessions = {}

class SessionData:
    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self.conversation_history = []
        self.document_context = None
        self.current_emotion = None
        self.audio_buffer = []
        self.created_at = datetime.now()

@app.get("/")
async def root():
    return {
        "message": "Mental Health AI Assistant API",
        "status": "running",
        "version": "2.0.0",
        "features": ["authentication", "database", "admin_dashboard", "appointments"]
    }

@app.post("/upload_document/")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process medical document"""
    try:
        # Save uploaded file temporarily
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        print(f"Processing document: {file.filename}")
        
        # Process document
        extracted_text = document_analyzer.process_document(temp_path)
        
        # Extract structured information
        if extracted_text:
            extracted_info = document_analyzer.extract_with_llm(extracted_text)
            if not extracted_info:
                extracted_info = document_analyzer.extract_medical_info(extracted_text)
            
            print(f"Extracted info: {len(extracted_info.get('medical_history', []))} medical history items")
        else:
            os.remove(temp_path)
            return JSONResponse(
                status_code=400,
                content={"error": "Could not extract text from document"}
            )
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        
        return {
            "status": "success",
            "document_info": extracted_info,
            "message": "Document processed successfully"
        }
    
    except Exception as e:
        print(f"Error processing document: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time analysis"""
    await websocket.accept()
    print(f"Client {session_id} connected")
    
    # Create session if not exists
    if session_id not in active_sessions:
        active_sessions[session_id] = SessionData()
    
    session = active_sessions[session_id]
    db = get_database()
    
    try:
        while True:
            # Receive data from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "authenticate":
                # Authenticate user via token
                token = message.get("token")
                try:
                    from auth.auth_handler import decode_jwt
                    payload = decode_jwt(token)
                    if payload:
                        session.user_id = payload.get("user_id")
                        await websocket.send_json({
                            "type": "authenticated",
                            "data": {"user_id": session.user_id}
                        })
                    else:
                        await websocket.send_json({
                            "type": "auth_error",
                            "data": {"message": "Invalid token"}
                        })
                except Exception as e:
                    await websocket.send_json({
                        "type": "auth_error",
                        "data": {"message": str(e)}
                    })
            
            elif message_type == "video_frame":
                # Process video frame for facial emotion
                frame_data = message.get("frame")
                emotion_result = await process_video_frame(frame_data, session)
                
                await websocket.send_json({
                    "type": "facial_emotion",
                    "data": emotion_result
                })
            
            # elif message_type == "audio_chunk":
            #     # Buffer audio chunks
            #     audio_data = message.get("audio")
            #     session.audio_buffer.append(audio_data)
            
            elif message_type == "audio_complete":
                # Process complete audio
                audio_data = message.get("audio")
                mime_type = message.get("mimeType", "audio/webm")
                size = message.get("size", 0)
                
                if not audio_data:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": "No audio data received"}
                    })
                    continue
    
                analysis_result = await process_audio(session, session_id, audio_data, mime_type)

                
                # Generate response
                if analysis_result and "transcribed_text" in analysis_result:
                    text = analysis_result["transcribed_text"]
                    print(f"Transcribed: {text}")
                    
                    if text:
                        # Get facial emotion
                        face_emotion = session.current_emotion
                        
                        # Perform multimodal analysis
                        response = await generate_response(text, face_emotion, analysis_result, session)
                        
                        # Save to database if user is authenticated
                        if session.user_id and DB_ENABLED:
                            try:
                                db = get_database()
                                await save_message(db, session_id, session.user_id, "user", text, face_emotion)
                                await save_message(db, session_id, session.user_id, "assistant", response.get("response", ""), None)
                            except Exception as e:
                                print(f"Database save error: {e}")
                                
                        await websocket.send_json({
                            "type": "analysis_complete",
                            "data": response
                        })
                        
                    else:
                        await websocket.send_json({
                            "type": "error",
                            "data": {"message": "Could not transcribe audio. Please try again."}
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "data": {"message": "Failed to process audio"}
                    })
                
                # Clear audio buffer
                session.audio_buffer = []
            
            elif message_type == "text_message":
                # Process text-only message
                text = message.get("text")
                face_emotion = session.current_emotion
                
                response = await generate_response(text, face_emotion, None, session)
                
                # Save to database if user is authenticated
                if session.user_id and DB_ENABLED:
                    try:
                        db = get_database()
                        await save_message(db, session_id, session.user_id, "user", text, face_emotion)
                        await save_message(db, session_id, session.user_id, "assistant", response.get("response", ""), None)
                    except Exception as e:
                        print(f"Database save error: {e}")
                await websocket.send_json({
                    "type": "response",
                    "data": response
                })
            
            elif message_type == "set_document_context":
                # Set document context for this session
                session.document_context = message.get("document_info")
                multimodal_analyzer.response_generator.set_document_context(session.document_context)
                print("Document context updated")
                
                await websocket.send_json({
                    "type": "context_updated",
                    "data": {"status": "Document context set"}
                })
            
            elif message_type == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        print(f"Client {session_id} disconnected")
    
    except Exception as e:
        print(f"Error in WebSocket: {str(e)}")
        try:
            await websocket.send_json({
                "type": "error",
                "data": {"message": str(e)}
            })
        except:
            pass

async def process_video_frame(frame_data: str, session: SessionData) -> dict:
    """Process a video frame for facial emotion detection"""
    try:
        # Decode base64 frame
        frame_bytes = base64.b64decode(frame_data.split(',')[1] if ',' in frame_data else frame_data)
        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        
        # Detect faces
        face_images, face_locations = face_detector.process_frame(frame)
        
        if face_images:
            # Use first face
            face_image = face_images[0]
            
            # Add to emotion analyzer
            emotion_analyzer.add_frame(face_image)
            
            # Get emotion if enough frames
            if len(emotion_analyzer.frame_buffer) >= 3:
                emotion_result = emotion_analyzer.get_emotion()
                session.current_emotion = emotion_result
                
                return {
                    "status": "success",
                    "emotion": emotion_result.get("emotion"),
                    "confidence": float(emotion_result.get("confidence", 0)),
                    "face_detected": True
                }
        
        return {
            "status": "no_face",
            "face_detected": False
        }
    
    except Exception as e:
        print(f"Error processing video frame: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

async def process_audio(session: SessionData, session_id: str, audio_data: str, mime_type: str = "audio/webm") -> dict:
    """Process complete audio recording"""
    try:
        if not audio_data:
            return {"status": "no_audio"}
        
        # Decode base64 audio
        audio_bytes = base64.b64decode(audio_data)
        
        print(f"Received audio: {len(audio_bytes)} bytes, type: {mime_type}")
        
        # Save to temporary file with correct extension
        temp_audio_dir = "temp_audio"
        os.makedirs(temp_audio_dir, exist_ok=True)
        
        # Determine file extension based on MIME type
        if 'webm' in mime_type:
            ext = 'webm'
        elif 'mp4' in mime_type:
            ext = 'm4a'
        elif 'ogg' in mime_type:
            ext = 'ogg'
        else:
            ext = 'webm'  # Default
        
        temp_input_path = os.path.join(temp_audio_dir, f"recording_{session_id}_{datetime.now().timestamp()}.{ext}")
        temp_wav_path = os.path.join(temp_audio_dir, f"recording_{session_id}_{datetime.now().timestamp()}.wav")
        
        # Save original audio
        with open(temp_input_path, 'wb') as f:
            f.write(audio_bytes)
        
        print(f"Saved audio to: {temp_input_path}")
        
        # Convert to WAV using pydub
        try:
            from pydub import AudioSegment
            
            # Load audio file
            if ext == 'webm':
                audio = AudioSegment.from_file(temp_input_path, format="webm")
            else:
                audio = AudioSegment.from_file(temp_input_path)
            
            # Convert to mono, 16kHz
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            
            # Export as WAV
            audio.export(temp_wav_path, format="wav")
            
            print(f"Converted to WAV: {temp_wav_path}")
            
        except ImportError:
            # Fallback: Try using ffmpeg directly
            import subprocess
            
            try:
                subprocess.run([
                    'ffmpeg', '-i', temp_input_path,
                    '-ar', '16000',
                    '-ac', '1',
                    '-y',
                    temp_wav_path
                ], check=True, capture_output=True)
                
                print(f"Converted with ffmpeg: {temp_wav_path}")
            except Exception as e:
                print(f"FFmpeg conversion failed: {e}")
                # Last resort: try to use original file
                temp_wav_path = temp_input_path
        
        # Analyze emotion
        print(f"Analyzing audio file: {temp_wav_path}")
        voice_result = voice_analyzer.analyze_emotion(temp_wav_path)
        
        # Clean up
        try:
            os.remove(temp_input_path)
            if os.path.exists(temp_wav_path) and temp_wav_path != temp_input_path:
                os.remove(temp_wav_path)
        except Exception as e:
            print(f"Cleanup error: {e}")
        
        return voice_result
    
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e)
        }

async def generate_response(text: str, face_emotion: dict, voice_result: dict, session: SessionData) -> dict:
    """Generate clinical response using multimodal analysis"""
    try:
        # Create a simple face analysis dict
        face_analysis = {}
        if face_emotion:
            face_analysis = {
                "emotion": face_emotion.get("emotion"),
                "confidence": float(face_emotion.get("confidence", 0))
            }
        
        # Analyze response with multimodal integration
        analysis = multimodal_analyzer.analyze_response(text, None, None)
        
        # Update face analysis
        if face_analysis:
            analysis["face_analysis"] = face_analysis
        
        # Add voice analysis if available
        if voice_result and "emotion" in voice_result:
            analysis["voice_analysis"] = {
                "emotion": voice_result.get("emotion"),
                "confidence": float(voice_result.get("confidence", 0)),
                "transcribed_text": voice_result.get("transcribed_text", "")
            }
        
        # Generate response
        response_data = multimodal_analyzer.generate_response(text, analysis)
        
        # Add to conversation history
        session.conversation_history.append({
            "role": "user",
            "content": text,
            "timestamp": datetime.now().isoformat()
        })
        session.conversation_history.append({
            "role": "assistant",
            "content": response_data.get("generated_response", {}).get("response", ""),
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "status": "success",
            "analysis": {
                "text": text,
                "facial_emotion": face_analysis,
                "voice_emotion": analysis.get("voice_analysis", {}),
                "intents": analysis.get("text_analysis", {}).get("intents", {}),
                "emotional_state": analysis.get("emotional_state", {}),
            },
            "response": response_data.get("generated_response", {}).get("response", ""),
            "suggested_followups": response_data.get("suggested_followups", [])
        }
    
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "response": "I apologize, but I'm having trouble processing that right now. Could you please try again?"
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "models_loaded": {
            "emotion_model": emotion_analyzer.model is not None,
            "intent_classifier": intent_classifier.classifier is not None,
            "voice_analyzer": True
        },
        "database_connected": get_database() is not None
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("Mental Health AI Assistant - Backend Server v2.0")
    print("="*50)
    print("Starting server on http://localhost:8000")
    print("WebSocket endpoint: ws://localhost:8000/ws/{session_id}")
    print("API Documentation: http://localhost:8000/docs")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)