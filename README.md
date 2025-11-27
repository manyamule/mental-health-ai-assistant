# 🧠 Mental Health AI Assistant

A multimodal AI-powered mental health assistant that uses facial emotion detection, voice analysis, and natural language processing to provide psychological support.

## 🌟 Features

- **Real-time Facial Emotion Detection** - Analyzes facial expressions using CNN model
- **Voice Emotion Analysis** - Processes speech tone and sentiment
- **AI-Powered Responses** - Uses Google Gemini for empathetic conversations
- **Medical Document Processing** - OCR extraction of medical records
- **Multimodal Integration** - Combines facial, voice, and text analysis
- **Text-to-Speech** - Natural voice responses using ElevenLabs
- **WebSocket Real-time Communication** - Instant updates and responses

## 🏗️ Tech Stack

### Backend
- **FastAPI** - Web framework
- **TensorFlow/Keras** - Emotion detection model
- **OpenCV** - Face detection
- **Librosa** - Audio feature extraction
- **Google Gemini 2.0** - AI responses
- **ElevenLabs** - Text-to-speech
- **PyTesseract** - OCR for documents

### Frontend
- **React** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **WebSocket** - Real-time communication
- **React Webcam** - Camera integration

## 📁 Project Structure
```
mental_health/
├── backend_app.py              # FastAPI WebSocket server
├── emotion_analysis/           # Emotion detection modules
├── intent_classification/      # Intent recognition
├── knowledge_base/            # Clinical knowledge
├── models/                    # Trained ML models
└── frontend/                  # React application
    ├── src/
    │   ├── components/
    │   ├── hooks/
    │   └── config.js
    └── package.json
```

## 🚀 Installation

### Prerequisites
- Python 3.8+
- Node.js 20+
- Webcam and microphone

### Backend Setup
```bash
cd mental_health
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Mac/Linux

pip install tensorflow keras opencv-python librosa scikit-learn nltk
pip install fastapi uvicorn websockets python-multipart
pip install google-generativeai elevenlabs
pip install pytesseract pdf2image Pillow pymupdf
pip install pyaudio speechrecognition vaderSentiment
```

### Frontend Setup
```bash
cd frontend
npm install
```

### Environment Variables

Create `.env` file in root:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
ELEVEN_API_KEY=your_elevenlabs_api_key_here
```

## 🎯 Running the Application

### Start Backend
```bash
cd mental_health
.venv\Scripts\activate
python backend_app.py
```

Backend runs on: `http://localhost:8000`

### Start Frontend
```bash
cd frontend
npm run dev
```

Frontend runs on: `http://localhost:3000`

## 📖 Usage

1. Open `http://localhost:3000` in your browser
2. (Optional) Upload medical document
3. Allow camera and microphone permissions
4. Start conversation with the AI assistant
5. Your emotions are analyzed in real-time

## 🔐 Security Notes

- Never commit `.env` file with API keys
- Use HTTPS in production
- Implement proper authentication for deployment
- Store sensitive data securely

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.



## 👨‍💻 Author

Manoj Mule  - B.Tech IT Student at VIT Pune

## 🙏 Acknowledgments

- TensorFlow for emotion detection
- Google Gemini for AI responses
- ElevenLabs for natural TTS
- OpenAI for inspiration

---

**⚠️ Disclaimer:** This is an educational project. For actual mental health concerns, please consult licensed professionals.
