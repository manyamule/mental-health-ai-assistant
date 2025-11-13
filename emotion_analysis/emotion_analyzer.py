import os
import cv2
import numpy as np
import tensorflow as tf

from keras.models import load_model
import time

class EmotionAnalyzer:
    def __init__(self, model_path="models/my_model.h5"):
        """
        Initialize the emotion analyzer with the trained model
        """
        self.model_path = model_path
        self.model = None
        self.emotions = {
            0: "surprise",
            1: "happy",
            2: "anger", 
            3: "sadness",
            4: "fear"
        }
        self.frame_buffer = []
        self.load_model()
        
    def load_model(self):
        """Load the trained emotion recognition model"""
        try:
            if os.path.exists(self.model_path):
                self.model = load_model(self.model_path)
                print("Emotion recognition model loaded successfully")
            else:
                print(f"Model file not found at {self.model_path}")
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            
    def preprocess_frame(self, frame):
        """Preprocess a frame for the model"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) > 2 else frame
            
            # Resize to 48x48
            resized = cv2.resize(gray, (48, 48))
            
            # Normalize
            normalized = resized / 255.0
            
            return normalized
        except Exception as e:
            print(f"Error in preprocessing frame: {str(e)}")
            return None
            
    def add_frame(self, frame):
        """Add a frame to the buffer for emotion analysis"""
        preprocessed = self.preprocess_frame(frame)
        if preprocessed is not None:
            self.frame_buffer.append(preprocessed)
            # Keep only the most recent 3 frames
            if len(self.frame_buffer) > 3:
                self.frame_buffer.pop(0)
                
    def get_emotion(self):
        """Analyze current frame buffer and return detected emotion"""
        if len(self.frame_buffer) < 3 or self.model is None:
            return {"status": "waiting", "message": "Need more frames or model not loaded"}
            
        try:
            # Prepare input in the format model expects: (1, 3, 48, 48, 1)
            input_data = np.array(self.frame_buffer[-3:])  # Take last 3 frames
            input_data = input_data.reshape(1, 3, 48, 48, 1)
            
            # Get prediction
            prediction = self.model.predict(input_data, verbose=0)
            emotion_idx = np.argmax(prediction[0])
            confidence = float(prediction[0][emotion_idx])
            
            result = {
                "emotion": self.emotions[emotion_idx],
                "confidence": confidence,
                "emotion_scores": {self.emotions[i]: float(score) for i, score in enumerate(prediction[0])},
                "timestamp": time.time()
            }
            
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def analyze_video_stream(self, video_capture, display=False, callback=None):
        """Process a video stream for emotion analysis"""
        if not video_capture.isOpened():
            print("Error: Could not open video stream.")
            return
            
        while True:
            ret, frame = video_capture.read()
            if not ret:
                break
                
            self.add_frame(frame)
            
            if len(self.frame_buffer) >= 3:
                emotion_result = self.get_emotion()
                
                if callback:
                    callback(emotion_result, frame)
                
                if display:
                    emotion_text = f"{emotion_result.get('emotion', 'unknown')}: {emotion_result.get('confidence', 0):.2f}"
                    cv2.putText(frame, emotion_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.imshow('Emotion Analysis', frame)
            
            # Press 'q' to quit
            if display and cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        if display:
            cv2.destroyAllWindows()
            
    def reset(self):
        """Reset the frame buffer"""
        self.frame_buffer = []