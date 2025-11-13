import os
import time
import threading
import cv2
import numpy as np
import pyttsx3  # Fallback TTS
import pygame
import tempfile
from dotenv import load_dotenv

# Correct ElevenLabs imports
from elevenlabs import Voice, VoiceSettings
from elevenlabs.client import ElevenLabs
# from elevenlabs.api import Models, Voices, Audio

from emotion_analyzer import EmotionAnalyzer
from face_detector import FaceDetector
from voice_analyzer import VoiceAnalyzer
from multimodal_integration import MultimodalAnalyzer
from parallel_analyzer import ParallelAnalyzer
from intent_classification.intent_classifier import IntentClassifier

class VoiceAssistant:
    def __init__(self):
        """Initialize the interactive voice assistant with specific Eleven Labs voice"""
        print("Initializing AI voice assistant...")
        
        # Load environment variables (for API keys)
        load_dotenv()
        
        # Initialize components
        self.emotion_analyzer = EmotionAnalyzer("models/my_model.h5")
        self.voice_analyzer = VoiceAnalyzer()
        self.intent_classifier = IntentClassifier(model_dir="../intent_classification/intent_models")
        self.face_detector = FaceDetector()
        self.multimodal_analyzer = MultimodalAnalyzer(
            self.emotion_analyzer, 
            self.intent_classifier, 
            self.voice_analyzer
        )
        self.parallel_analyzer = ParallelAnalyzer(
            self.emotion_analyzer, 
            self.voice_analyzer, 
            self.multimodal_analyzer
        )
        
        # Initialize Eleven Labs for TTS with specific voice ID
        self.eleven_api_key = os.getenv("ELEVEN_API_KEY")
        self.voice_id = "y6Ao4Y93UrnTbmzdVlFc"# (<-vikrant)"Qc0h5B5Mqs8oaH4sFZ9X"(<-sagar) #"H8bdWZHK2OgZwTN7ponr" # Using the specific voice ID
        
        if not self.eleven_api_key:
            print("Warning: No Eleven Labs API key found. Falling back to basic TTS.")
            # Initialize the fallback TTS engine
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 0.9)
            
            # Try to use a female voice if available
            voices = self.tts_engine.getProperty('voices')
            for voice in voices:
                if 'female' in voice.name.lower():
                    self.tts_engine.setProperty('voice', voice.id)
                    break
            
            self.tts_method = "pyttsx3"
        else:
            # Initialize ElevenLabs client with API key
            self.eleven_client = ElevenLabs(api_key=self.eleven_api_key)
            print(f"Eleven Labs API initialized with voice ID: {self.voice_id}")
            
            # Initialize pygame for audio playback
            pygame.mixer.init()
            self.tts_method = "elevenlabs"
        
        # Runtime variables
        self.running = False
        self.conversation_active = False
        self.last_analysis_result = None
        self.last_response = None
        self.is_speaking = False
        
        print("AI voice assistant initialized.")
    
    def _speak_response(self, text):
        """Convert text to speech using Eleven Labs with specific voice ID"""
        if not text:
            return
            
        self.is_speaking = True
        
        try:
            # Use Eleven Labs if available
            if self.tts_method == "elevenlabs":
                print("Generating speech with Eleven Labs...")
                
                # Adapt voice based on emotional context
                stability = 0.71
                similarity_boost = 0.5
                
                # If we have emotional analysis, adjust voice parameters
                if self.last_analysis_result and 'emotional_state' in self.last_analysis_result:
                    state = self.last_analysis_result['emotional_state']
                    if 'valence' in state and 'arousal' in state:
                        # Higher stability for negative emotions for more controlled delivery
                        if state['valence'] < -0.3:
                            stability = 0.85
                        
                        # More expressiveness for positive emotions
                        if state['valence'] > 0.3:
                            stability = 0.65
                
                # Set voice settings
                voice_settings = VoiceSettings(
                    stability=stability,
                    similarity_boost=similarity_boost
                )
                
                # Generate audio with Eleven Labs using specific voice ID and new API
                audio_chunks = self.eleven_client.generate(
                    text=text,
                    voice=self.voice_id,
                    model="eleven_turbo_v2",
                    voice_settings=voice_settings
                )

                audio_bytes = b"".join(audio_chunks)
                
                # Save to temporary file for pygame playback
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                    temp_file.write(audio_bytes)
                    temp_path = temp_file.name
                
                # Play the audio
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                
                # Wait for the audio to finish playing
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                    
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
            else:
                # Fallback to pyttsx3
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                
        except Exception as e:
            print(f"Error during speech synthesis: {e}")
            # Try fallback if Eleven Labs fails
            if self.tts_method == "elevenlabs":
                print("Falling back to basic TTS...")
                try:
                    if not hasattr(self, 'tts_engine'):
                        self.tts_engine = pyttsx3.init()
                        self.tts_engine.setProperty('rate', 150)
                    self.tts_engine.say(text)
                    self.tts_engine.runAndWait()
                except:
                    print("All TTS methods failed")
        
        finally:
            self.is_speaking = False

    def start(self):
        """Start the voice assistant"""
        if self.running:
            print("Voice assistant is already running")
            return
        
        self.running = True
        
        # Start webcam
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open webcam")
            self.running = False
            return
        
        # Start parallel analysis for continuous processing
        self.parallel_analyzer.start_processing(callback=self._process_analysis_result)
        
        print("\n==== AI Voice Assistant Active ====")
        print("I'll listen for your voice and analyze your facial expressions.")
        print("Speak naturally, and I'll respond when you finish talking.")
        print("Press 'q' to quit, 'r' to reset conversation.")
        
        # Main loop
        try:
            while self.running:
                # Read frame
                ret, frame = self.cap.read()
                if not ret:
                    print("Error reading from webcam")
                    break
                
                # Detect faces
                face_images, face_locations = self.face_detector.process_frame(frame)
                
                # Use the first face if detected
                if face_images:
                    face_image = face_images[0]
                    face_location = face_locations[0]
                    
                    # Add rectangle around face
                    x, y, w, h = face_location
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # Add frame to parallel analyzer
                    self.parallel_analyzer.add_frame(face_image)
                
                # Add status information to frame
                self._add_status_to_frame(frame)
                
                # Display the frame
                cv2.imshow('AI Assistant', frame)
                
                # Process keyboard input
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('r'):
                    self._reset_conversation()
                
                # Small delay to reduce CPU usage
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("Stopped by user")
        finally:
            self.stop()
    
    def _process_analysis_result(self, result):
        """Process analysis results from speech"""
        if not result:
            return
        
        # Store the result
        self.last_analysis_result = result
        
        # Only generate and speak response if not already speaking
        if not self.is_speaking:
            # Generate a response using the LLM if needed
            if 'generated_response' not in result:
                text = result.get('voice_analysis', {}).get('transcribed_text', '')
                if text:
                    result = self.multimodal_analyzer.generate_response(text, result)
            
            # Get and display the response
            if 'generated_response' in result and 'response' in result['generated_response']:
                response_text = result['generated_response']['response']
                self.last_response = response_text
                
                # Print the response text
                print("\n🤖 Assistant: " + response_text)
                
                # Speak the response in a separate thread
                threading.Thread(target=self._speak_response, args=(response_text,)).start()
    
    def _add_status_to_frame(self, frame):
        """Add status overlay to the video frame"""
        # Frame dimensions
        height, width = frame.shape[:2]
        
        # Status bar background
        cv2.rectangle(frame, (0, height-80), (width, height), (0, 0, 0), -1)
        cv2.rectangle(frame, (0, 0), (width, 40), (0, 0, 0), -1)
        
        # System status
        cv2.putText(frame, "AI Assistant: Active", (10, 25), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Show speaking status
        if self.is_speaking:
            cv2.putText(frame, "Speaking...", (width-150, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
        elif self.parallel_analyzer.speaking:
            cv2.putText(frame, "Listening...", (width-150, 25), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Show detected emotion if available
        if self.last_analysis_result:
            # Facial emotion
            if 'face_analysis' in self.last_analysis_result and 'emotion' in self.last_analysis_result['face_analysis']:
                face_emotion = self.last_analysis_result['face_analysis']['emotion']
                cv2.putText(frame, f"Facial emotion: {face_emotion}", (10, height-55), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Voice emotion
            if 'voice_analysis' in self.last_analysis_result and self.last_analysis_result['voice_analysis']:
                voice_data = self.last_analysis_result['voice_analysis']
                
                if 'emotion' in voice_data:
                    voice_emotion = voice_data['emotion']
                    cv2.putText(frame, f"Voice emotion: {voice_emotion}", (10, height-30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                # Show last transcribed text
                if 'transcribed_text' in voice_data and voice_data['transcribed_text']:
                    text = voice_data['transcribed_text']
                    # Truncate if too long
                    if len(text) > 60:
                        text = text[:57] + "..."
                    cv2.putText(frame, f"You: {text}", (10, height-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Show the last response
        if self.last_response and self.is_speaking:
            # Display a shortened version of the response
            short_response = self.last_response[:50] + "..." if len(self.last_response) > 50 else self.last_response
            cv2.putText(frame, f"Assistant: {short_response}", (width//2-200, 70), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
    
    def _reset_conversation(self):
        """Reset the conversation state"""
        if hasattr(self, 'multimodal_analyzer'):
            self.multimodal_analyzer.reset_session()
        self.last_analysis_result = None
        self.last_response = None
        print("\n===== Conversation Reset =====")
    
    def stop(self):
        """Stop the voice assistant"""
        self.running = False
        
        # Stop text-to-speech if active
        if self.is_speaking:
            if hasattr(self, 'tts_engine'):
                self.tts_engine.stop()
            pygame.mixer.music.stop()
        
        # Stop parallel analysis
        if hasattr(self, 'parallel_analyzer'):
            self.parallel_analyzer.stop_processing()
        
        # Release resources
        if hasattr(self, 'cap') and self.cap is not None:
            self.cap.release()
        
        cv2.destroyAllWindows()
        print("Voice assistant stopped")