from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile
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

# Get the directory where this script is located
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Change to the script directory
os.chdir(current_dir)

print(f"Working directory: {os.getcwd()}")
print(f"Python path includes: {current_dir}")

# Import modules
try:
    from emotion_analysis.emotion_analyzer import EmotionAnalyzer
    from emotion_analysis.voice_analyzer import VoiceAnalyzer
    from emotion_analysis.face_detector import FaceDetector
    from emotion_analysis.multimodal_integration import MultimodalAnalyzer
    from emotion_analysis.document_analyzer import DocumentAnalyzer
    from intent_classification.intent_classifier import IntentClassifier
    print("✓ All modules imported successfully")
except ImportError as e:
    print(f"✗ Import Error: {e}")
    print(f"Make sure you're running from: {current_dir}")
    print("Directory structure should be:")
    print("  D:/mental_health/")
    print("    ├── backend_app.py")
    print("    ├── emotion_analysis/")
    print("    └── intent_classification/")
    sys.exit(1)

app = FastAPI(title="Mental Health AI Assistant API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize analyzers
print("Loading models...")
emotion_analyzer = EmotionAnalyzer("models/my_model.h5")
voice_analyzer = VoiceAnalyzer()
face_detector = FaceDetector()
intent_classifier = IntentClassifier(model_dir="intent_classification/intent_models")
multimodal_analyzer = MultimodalAnalyzer(emotion_analyzer, intent_classifier, voice_analyzer)
document_analyzer = DocumentAnalyzer()
print("Models loaded successfully!")

# Store active sessions
active_sessions = {}

class SessionData:
    def __init__(self):
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
        "version": "1.0.0"
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
            # Try using LLM extraction first, fallback to regex
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
    
    try:
        while True:
            # Receive data from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            
            if message_type == "video_frame":
                # Process video frame for facial emotion
                frame_data = message.get("frame")
                emotion_result = await process_video_frame(frame_data, session)
                
                await websocket.send_json({
                    "type": "facial_emotion",
                    "data": emotion_result
                })
            
            elif message_type == "audio_chunk":
                # Buffer audio chunks
                audio_data = message.get("audio")
                session.audio_buffer.append(audio_data)
            
            elif message_type == "audio_complete":
                # Process complete audio
                print("Processing audio...")
                analysis_result = await process_audio(session, session_id)
                
                # Generate response
                if analysis_result and "transcribed_text" in analysis_result:
                    text = analysis_result["transcribed_text"]
                    print(f"Transcribed: {text}")
                    
                    if text:
                        # Get facial emotion
                        face_emotion = session.current_emotion
                        
                        # Perform multimodal analysis
                        response = await generate_response(text, face_emotion, analysis_result, session)
                        
                        await websocket.send_json({
                            "type": "analysis_complete",
                            "data": response
                        })
                
                # Clear audio buffer
                session.audio_buffer = []
            
            elif message_type == "text_message":
                # Process text-only message
                text = message.get("text")
                face_emotion = session.current_emotion
                
                response = await generate_response(text, face_emotion, None, session)
                
                await websocket.send_json({
                    "type": "response",
                    "data": response
                })
            
            elif message_type == "set_document_context":
                # Set document context for this session
                session.document_context = message.get("document_info")
                # Set in response generator
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

async def process_audio(session: SessionData, session_id: str) -> dict:
    """Process buffered audio chunks"""
    try:
        if not session.audio_buffer:
            return {"status": "no_audio"}
        
        # Combine audio chunks
        audio_data = b''.join([base64.b64decode(chunk) for chunk in session.audio_buffer])
        
        # Save to temporary WAV file
        temp_audio_dir = "temp_audio"
        os.makedirs(temp_audio_dir, exist_ok=True)
        temp_audio_path = os.path.join(temp_audio_dir, f"recording_{session_id}_{datetime.now().timestamp()}.wav")
        
        with wave.open(temp_audio_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(16000)
            wf.writeframes(audio_data)
        
        print(f"Analyzing audio file: {temp_audio_path}")
        
        # Analyze emotion
        voice_result = voice_analyzer.analyze_emotion(temp_audio_path)
        
        # Clean up
        try:
            os.remove(temp_audio_path)
        except:
            pass
        
        return voice_result
    
    except Exception as e:
        print(f"Error processing audio: {str(e)}")
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
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*50)
    print("Mental Health AI Assistant - Backend Server")
    print("="*50)
    print("Starting server on http://localhost:8000")
    print("WebSocket endpoint: ws://localhost:8000/ws/{session_id}")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)