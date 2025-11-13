import cv2
import numpy as np
import time
import os
from emotion_analyzer import EmotionAnalyzer
from face_detector import FaceDetector

def test_with_camera():
    """Test emotion analysis with webcam"""
    # Check if model file exists
    model_path = "models/my_model.h5"
    if not os.path.exists(model_path):
        print(f"Model file not found at {model_path}")
        print("Please ensure you've copied your trained model to this location.")
        return
    
    # Initialize components
    emotion_analyzer = EmotionAnalyzer(model_path)
    face_detector = FaceDetector()
    
    # Start webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Could not open webcam")
        return
        
    print("Starting emotion analysis... Press 'q' to quit.")
    
    frame_count = 0
    start_time = time.time()
    
    while True:
        # Read frame
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
            
        # Detect faces
        face_images, face_locations = face_detector.process_frame(frame)
        
        # Process each detected face
        for i, (face_img, face_loc) in enumerate(zip(face_images, face_locations)):
            # Add frame to emotion analyzer
            emotion_analyzer.add_frame(face_img)
            
            # Get emotion if we have enough frames
            if len(emotion_analyzer.frame_buffer) >= 3:
                emotion_result = emotion_analyzer.get_emotion()
                
                # Display result on frame
                if 'emotion' in emotion_result:
                    x, y, w, h = face_loc
                    emotion = emotion_result['emotion']
                    confidence = emotion_result['confidence']
                    
                    # Draw rectangle around face
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # Display emotion label
                    text = f"{emotion}: {confidence:.2f}"
                    cv2.putText(frame, text, (x, y-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    
                    # Print emotion data
                    print(f"Face {i}: {text}")
        
        # Display the frame
        cv2.imshow('Emotion Analysis', frame)
        
        frame_count += 1
        
        # Calculate and display FPS every second
        if time.time() - start_time >= 1:
            fps = frame_count / (time.time() - start_time)
            print(f"FPS: {fps:.2f}")
            frame_count = 0
            start_time = time.time()
        
        # Break loop on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release resources
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_with_camera()