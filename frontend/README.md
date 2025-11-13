# Mental Health AI Assistant - Frontend

React-based web interface for the multimodal mental health analysis system.

## Prerequisites

- Node.js 18+ and npm
- Backend server running on port 8000

## Installation
```bash
npm install
```

## Development
```bash
npm run dev
```

Open http://localhost:3000 in your browser.

## Features

- 📹 Real-time facial emotion detection via webcam
- 🎤 Voice recording and emotion analysis
- 💬 Chat interface with AI psychiatrist
- 📄 Medical document upload and analysis
- 📊 Emotion visualization dashboard
- 🔄 WebSocket real-time communication

## Browser Requirements

- Modern browser with WebRTC support
- Camera and microphone permissions
- WebSocket support

## Configuration

Edit `src/config.js` to change API endpoints:
```javascript
export const API_BASE_URL = 'http://localhost:8000';
export const WS_BASE_URL = 'ws://localhost:8000';
```