import os
import sys

# Set working directory
os.chdir(r'D:\mental_health')
sys.path.insert(0, r'D:\mental_health')

print("Working directory:", os.getcwd())
print("Python path:", sys.path[0])

# Test imports one by one
try:
    print("\n1. Testing emotion_analyzer import...")
    from emotion_analysis.emotion_analyzer import EmotionAnalyzer
    print("   ✓ EmotionAnalyzer imported")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

try:
    print("2. Testing voice_analyzer import...")
    from emotion_analysis.voice_analyzer import VoiceAnalyzer
    print("   ✓ VoiceAnalyzer imported")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

try:
    print("3. Testing face_detector import...")
    from emotion_analysis.face_detector import FaceDetector
    print("   ✓ FaceDetector imported")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

try:
    print("4. Testing multimodal_integration import...")
    from emotion_analysis.multimodal_integration import MultimodalAnalyzer
    print("   ✓ MultimodalAnalyzer imported")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

try:
    print("5. Testing intent_classifier import...")
    from intent_classification.intent_classifier import IntentClassifier
    print("   ✓ IntentClassifier imported")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

print("\n✓✓✓ All imports successful! ✓✓✓\n")

# Now start the actual server
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"status": "Backend is running!", "message": "All modules loaded successfully"}

if __name__ == "__main__":
    print("Starting FastAPI server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)