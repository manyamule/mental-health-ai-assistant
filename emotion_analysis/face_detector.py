import cv2
import numpy as np

class FaceDetector:
    def __init__(self, face_cascade_path="haarcascade_frontalface_default.xml"):
        """Initialize face detector with cascade classifier"""
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + face_cascade_path)
        
    def detect_faces(self, frame):
        """Detect faces in a frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) > 2 else frame
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        return faces
    
    def extract_face(self, frame, face_rect, target_size=(48, 48)):
        """Extract and preprocess a face region from the frame"""
        x, y, w, h = face_rect
        face_region = frame[y:y+h, x:x+w]
        
        # Convert to grayscale if not already
        gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY) if len(face_region.shape) > 2 else face_region
        
        # Resize to target size
        resized_face = cv2.resize(gray_face, target_size)
        
        return resized_face, (x, y, w, h)
    
    def process_frame(self, frame):
        """Detect and extract all faces in a frame"""
        faces = self.detect_faces(frame)
        face_images = []
        face_locations = []
        
        for face in faces:
            face_img, face_loc = self.extract_face(frame, face)
            face_images.append(face_img)
            face_locations.append(face_loc)
            
        return face_images, face_locations