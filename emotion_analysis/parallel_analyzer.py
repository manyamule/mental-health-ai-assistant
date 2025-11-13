import threading
import queue
import time
import numpy as np
import cv2
import pyaudio
import wave
import os
from collections import deque

class ParallelAnalyzer:
    def __init__(self, emotion_analyzer, voice_analyzer, multimodal_analyzer):
        """Initialize parallel processing of facial expressions and voice"""
        self.emotion_analyzer = emotion_analyzer
        self.voice_analyzer = voice_analyzer
        self.multimodal_analyzer = multimodal_analyzer
        
        # Video processing
        self.video_thread = None
        self.video_running = False
        self.frame_queue = queue.Queue(maxsize=10)
        self.processed_frames = deque(maxlen=30)  # Store last 30 processed frames
        self.current_emotion = None
        
        # Audio processing
        self.audio_thread = None
        self.audio_running = False
        self.audio_queue = queue.Queue()
        self.temp_dir = "temp_audio"
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paInt16
        self.speaking = False
        self.speech_frames = []
        self.silence_threshold = 0.01  # Adjust based on your microphone sensitivity
        self.silence_limit = 1.0  # Seconds of silence before ending speech detection
        self.speech_limit = 10.0  # Maximum speech recording time in seconds
        
        # Results
        self.latest_results = {}
        self.results_callback = None
        
        # Create temp directory if it doesn't exist
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
    
    def start_processing(self, callback=None):
        """Start parallel processing of video and audio"""
        self.results_callback = callback
        
        # Start video thread
        self.video_running = True
        self.video_thread = threading.Thread(target=self._process_video)
        self.video_thread.daemon = True
        self.video_thread.start()
        
        # Start audio thread
        self.audio_running = True
        self.audio_thread = threading.Thread(target=self._process_audio)
        self.audio_thread.daemon = True
        self.audio_thread.start()
        
        print("Parallel analysis started")
    
    def stop_processing(self):
        """Stop all parallel processing"""
        self.video_running = False
        self.audio_running = False
        
        if self.video_thread:
            self.video_thread.join(timeout=1.0)
        
        if self.audio_thread:
            self.audio_thread.join(timeout=1.0)
        
        print("Parallel analysis stopped")
    
    def add_frame(self, frame):
        """Add a video frame for processing"""
        if not self.frame_queue.full():
            self.frame_queue.put(frame)
    
    def get_latest_processed_frame(self):
        """Get the latest processed frame with emotion overlay"""
        if self.processed_frames:
            return self.processed_frames[-1]
        return None
    
    def _process_video(self):
        """Process video frames for facial emotion analysis"""
        while self.video_running:
            try:
                if not self.frame_queue.empty():
                    frame = self.frame_queue.get(timeout=0.1)
                    
                    # Add frame to emotion analyzer
                    self.emotion_analyzer.add_frame(frame)
                    
                    # Get emotion if enough frames collected
                    if len(self.emotion_analyzer.frame_buffer) >= 3:
                        emotion_result = self.emotion_analyzer.get_emotion()
                        
                        if 'emotion' in emotion_result:
                            self.current_emotion = emotion_result
                            
                            # Add emotion label to frame
                            emotion = emotion_result['emotion']
                            confidence = emotion_result['confidence']
                            
                            # Create a copy of the frame for display
                            display_frame = frame.copy()
                            text = f"{emotion}: {confidence:.2f}"
                            cv2.putText(display_frame, text, (10, 30), 
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            
                            # Add speaking indicator if currently speaking
                            if self.speaking:
                                cv2.putText(display_frame, "Speaking...", (10, 60), 
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                            
                            # Store processed frame
                            self.processed_frames.append(display_frame)
                    else:
                        # No emotion detected yet, just store original frame
                        self.processed_frames.append(frame)
                    
                    # Mark frame as processed
                    self.frame_queue.task_done()
                else:
                    # Wait a bit if no frames to process
                    time.sleep(0.01)
                    
            except Exception as e:
                print(f"Error processing video frame: {e}")
                time.sleep(0.1)
    
    def _process_audio(self):
        """Process audio for speech detection and analysis"""
        # Initialize PyAudio
        audio = pyaudio.PyAudio()
        
        # Open audio stream
        stream = audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        # Variables for speech detection
        silent_frames = 0
        speech_frames_count = 0
        max_silent_frames = int(self.silence_limit * self.sample_rate / self.chunk_size)
        max_speech_frames = int(self.speech_limit * self.sample_rate / self.chunk_size)
        
        print("Audio processing started")
        
        try:
            while self.audio_running:
                # Read audio chunk
                data = stream.read(self.chunk_size)
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # Check if speech detected (simple energy-based detection)
                energy = np.sum(np.abs(audio_data)) / len(audio_data)
                energy_normalized = energy / 32768.0  # Normalize by max int16 value
                
                if energy_normalized > self.silence_threshold:
                    # Speech detected
                    if not self.speaking:
                        print("Speech detected, recording...")
                        self.speaking = True
                        self.speech_frames = []  # Reset speech frames
                    
                    # Add frame to speech
                    self.speech_frames.append(data)
                    speech_frames_count += 1
                    silent_frames = 0
                    
                    # Check if maximum speech duration reached
                    if speech_frames_count >= max_speech_frames:
                        print("Maximum speech duration reached")
                        self._process_speech()
                        speech_frames_count = 0
                        
                elif self.speaking:
                    # Track silence during speech
                    self.speech_frames.append(data)
                    silent_frames += 1
                    speech_frames_count += 1
                    
                    # End of speech if silence limit reached
                    if silent_frames >= max_silent_frames:
                        print("End of speech detected")
                        self._process_speech()
                        speech_frames_count = 0
                        silent_frames = 0
                
                # Sleep a tiny bit to reduce CPU usage
                time.sleep(0.001)
                
        except Exception as e:
            print(f"Error processing audio: {e}")
        
        finally:
            # Clean up
            stream.stop_stream()
            stream.close()
            audio.terminate()
            print("Audio processing stopped")
    
    def _process_speech(self):
        """Process detected speech"""
        if not self.speech_frames:
            self.speaking = False
            return
        
        try:
            # Create unique filename
            filename = os.path.join(self.temp_dir, f"speech_{int(time.time())}.wav")
            
            # Save speech to WAV file
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.speech_frames))
            wf.close()
            
            print(f"Speech saved to {filename}")
            
            # Analyze the speech
            speech_analysis = self.voice_analyzer.analyze_emotion(filename)
            
            # Get current facial emotion
            face_emotion = self.current_emotion
            
            # Get text from speech
            text = speech_analysis.get('transcribed_text', '')
            
            if text:
                print(f"Transcribed: \"{text}\"")
                
                # Perform multimodal analysis
                face_image = self.processed_frames[-1] if self.processed_frames else None
                
                if text and face_image is not None:
                    # Get current facial emotion
                    face_emotion = self.current_emotion
                    
                    # Perform multimodal analysis
                    result = self.multimodal_analyzer.analyze_response(text, face_image, filename)
                    
                    # Generate response using LLM
                    result_with_response = self.multimodal_analyzer.generate_response(text, result)
                    
                    self.latest_results = result_with_response
                    
                    # Call callback if provided
                    if self.results_callback:
                        self.results_callback(result_with_response)
                    
                    # Print analysis summary
                    print("\n----- REAL-TIME ANALYSIS -----")
                    print(f"Text: \"{text}\"")
                    
                    # Face emotion
                    if face_emotion and 'emotion' in face_emotion:
                        print(f"Face emotion: {face_emotion['emotion']} ({face_emotion['confidence']:.2f})")
                    
                    # Voice emotion
                    if 'emotion' in speech_analysis:
                        print(f"Voice emotion: {speech_analysis['emotion']} ({speech_analysis['confidence']:.2f})")
                    
                    # Overall emotional state
                    if 'emotional_state' in result_with_response and result_with_response['emotional_state']['dominant_emotion']:
                        state = result_with_response['emotional_state']
                        print(f"Dominant emotion: {state['dominant_emotion']}")
            
            # Reset speech state
            self.speaking = False
            self.speech_frames = []
            
        except Exception as e:
            print(f"Error processing speech: {e}")
            self.speaking = False
            self.speech_frames = []