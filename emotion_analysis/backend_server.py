from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import shutil
import os

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/analyze_audio/")
async def analyze_audio(file: UploadFile = File(...)):
    print(f"Received audio file: {file.filename}")
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # TODO: Run your audio analysis here, e.g.:
    # emotion, transcript = analyze_audio_file(file_path)
    # For demo:
    emotion, transcript = "happy", "Hello from backend!"
    return JSONResponse({"emotion": emotion, "transcript": transcript})

@app.post("/analyze_image/")
async def analyze_image(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # TODO: Run your image analysis here, e.g.:
    # emotion = analyze_image_file(file_path)
    # For demo:
    emotion = "surprised"
    return JSONResponse({"emotion": emotion})
