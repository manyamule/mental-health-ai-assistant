import { useState, useCallback, useRef, useEffect } from 'react';
import { DocumentUpload } from './components/DocumentUpload';
import { VideoPanel } from './components/VideoPanel';
import { ChatPanel } from './components/ChatPanel';
import { EmotionDisplay } from './components/EmotionDisplay';
import { useWebSocket } from './hooks/useWebSocket';
import { Activity } from 'lucide-react';

function App() {
  const [showDocumentUpload, setShowDocumentUpload] = useState(true);
  const [documentContext, setDocumentContext] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [facialEmotion, setFacialEmotion] = useState(null);
  const [voiceEmotion, setVoiceEmotion] = useState(null);
  const [overallState, setOverallState] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // WebSocket message handler
  const handleWebSocketMessage = useCallback((data) => {
    console.log('Received:', data);

    switch (data.type) {
      case 'facial_emotion':
        if (data.data.status === 'success') {
          setFacialEmotion({
            emotion: data.data.emotion,
            confidence: data.data.confidence,
          });
        }
        break;

      case 'analysis_complete':
      case 'response':
        const analysisData = data.data;
        
        // Update emotions
        if (analysisData.analysis) {
          if (analysisData.analysis.facial_emotion) {
            setFacialEmotion(analysisData.analysis.facial_emotion);
          }
          if (analysisData.analysis.emotional_state) {
            setOverallState(analysisData.analysis.emotional_state);
          }
        }

        // Add assistant message
        if (analysisData.response) {
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: analysisData.response,
              timestamp: new Date(),
            },
          ]);

          // Speak the response
          speakText(analysisData.response);
        }
        break;

      default:
        break;
    }
  }, []);

  const { isConnected, sendMessage, sessionId } = useWebSocket(handleWebSocketMessage);

  // Document upload handlers
  const handleDocumentProcessed = (docInfo) => {
    setDocumentContext(docInfo);
    setShowDocumentUpload(false);

    // Send document context to backend
    sendMessage({
      type: 'set_document_context',
      document_info: docInfo,
    });

    // Add welcome message
    setMessages([
      {
        role: 'assistant',
        content: "Hello! I'm Dr. Murli Prasad Sharma, your AI mental health assistant. I've reviewed your medical document. How are you feeling today?",
        timestamp: new Date(),
      },
    ]);
  };

  const handleSkipDocument = () => {
    setShowDocumentUpload(false);
    setMessages([
      {
        role: 'assistant',
        content: "Hello! I'm Dr. Murli Prasad Sharma, your AI mental health assistant. How can I help you today?",
        timestamp: new Date(),
      },
    ]);
  };

  // Video frame handler
  const handleVideoFrame = useCallback(
    (frameData) => {
      if (isConnected) {
        sendMessage({
          type: 'video_frame',
          frame: frameData,
        });
      }
    },
    [isConnected, sendMessage]
  );

  // Text message handler
  const handleSendMessage = (text) => {
    // Add user message to chat
    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: text,
        timestamp: new Date(),
      },
    ]);

    // Send to backend
    sendMessage({
      type: 'text_message',
      text: text,
    });
  };

  // Voice recording handlers
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
          
          // Convert to base64 and send
          const reader = new FileReader();
          reader.readAsDataURL(event.data);
          reader.onloadend = () => {
            const base64Audio = reader.result.split(',')[1];
            sendMessage({
              type: 'audio_chunk',
              audio: base64Audio,
            });
          };
        }
      };

      mediaRecorder.onstop = () => {
        // Signal audio complete
        sendMessage({
          type: 'audio_complete',
        });

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleVoiceToggle = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  // Text-to-Speech (using Web Speech API as fallback)
  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 1;
      
      // Try to use a better voice
      const voices = speechSynthesis.getVoices();
      const preferredVoice = voices.find(
        (voice) => voice.name.includes('Female') || voice.name.includes('Samantha')
      );
      if (preferredVoice) {
        utterance.voice = preferredVoice;
      }

      speechSynthesis.speak(utterance);
    }
  };

  // Load voices
  useEffect(() => {
    if ('speechSynthesis' in window) {
      speechSynthesis.getVoices();
    }
  }, []);

  if (showDocumentUpload) {
    return (
      <DocumentUpload
        onDocumentProcessed={handleDocumentProcessed}
        onSkip={handleSkipDocument}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-blue-600 p-2 rounded-lg">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Mental Health AI Assistant
                </h1>
                <p className="text-sm text-gray-500">Session: {sessionId.slice(0, 16)}...</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <div
                className={`px-3 py-1 rounded-full text-xs font-medium ${
                  isConnected
                    ? 'bg-green-100 text-green-700'
                    : 'bg-red-100 text-red-700'
                }`}
              >
                {isConnected ? '● Connected' : '● Disconnected'}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Video & Emotions */}
          <div className="space-y-6">
            <VideoPanel onFrame={handleVideoFrame} isConnected={isConnected} />
            <EmotionDisplay
              facialEmotion={facialEmotion}
              voiceEmotion={voiceEmotion}
              overallState={overallState}
            />
          </div>

          {/* Right Column - Chat */}
          <div className="lg:col-span-2 h-[calc(100vh-180px)]">
            <ChatPanel
              messages={messages}
              onSendMessage={handleSendMessage}
              onVoiceToggle={handleVoiceToggle}
              isRecording={isRecording}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;