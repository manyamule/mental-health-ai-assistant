import { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '../components/Navbar';
import { DocumentUpload } from '../components/DocumentUpload';
import { VideoPanel } from '../components/VideoPanel';
import { ChatPanel } from '../components/ChatPanel';
import { EmotionDisplay } from '../components/EmotionDisplay';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAuth } from '../context/AuthContext';
import { sessionAPI } from '../utils/api';
import { Activity, ArrowLeft } from 'lucide-react';
import { generateSessionId } from '../config';

export const ChatPage = () => {
  const [showDocumentUpload, setShowDocumentUpload] = useState(true);
  const [documentContext, setDocumentContext] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [facialEmotion, setFacialEmotion] = useState(null);
  const [voiceEmotion, setVoiceEmotion] = useState(null);
  const [overallState, setOverallState] = useState(null);
  const [currentSessionId] = useState(() => generateSessionId());
  
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const sessionStartedRef = useRef(false);

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
        
        if (analysisData.analysis) {
          if (analysisData.analysis.facial_emotion) {
            setFacialEmotion(analysisData.analysis.facial_emotion);
          }
          if (analysisData.analysis.emotional_state) {
            setOverallState(analysisData.analysis.emotional_state);
          }
        }

        if (analysisData.response) {
          setMessages((prev) => [
            ...prev,
            {
              role: 'assistant',
              content: analysisData.response,
              timestamp: new Date(),
            },
          ]);

          speakText(analysisData.response);
        }
        break;

      default:
        break;
    }
  }, []);

  const { isConnected, sendMessage, sessionId } = useWebSocket(handleWebSocketMessage);

  // Authenticate WebSocket on connection
  useEffect(() => {
    if (isConnected && token && !sessionStartedRef.current) {
      sendMessage({
        type: 'authenticate',
        token: token
      });
      sessionStartedRef.current = true;
    }
  }, [isConnected, token, sendMessage]);

  // Start session in database
  useEffect(() => {
    if (user && !showDocumentUpload && !sessionStartedRef.current) {
      startDatabaseSession();
    }
  }, [user, showDocumentUpload]);

  const startDatabaseSession = async () => {
    try {
      await sessionAPI.startSession(currentSessionId, documentContext);
      console.log('Session started in database');
    } catch (error) {
      console.error('Failed to start session:', error);
    }
  };

  const handleDocumentProcessed = (docInfo) => {
    setDocumentContext(docInfo);
    setShowDocumentUpload(false);

    sendMessage({
      type: 'set_document_context',
      document_info: docInfo,
    });

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

  const handleSendMessage = (text) => {
    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: text,
        timestamp: new Date(),
      },
    ]);

    sendMessage({
      type: 'text_message',
      text: text,
    });
  };

  const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: {
        channelCount: 1,
        sampleRate: 16000,
        echoCancellation: true,
        noiseSuppression: true
      } 
    });

    // Check supported MIME types
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : 'audio/webm';

    const mediaRecorder = new MediaRecorder(stream, { mimeType });
    mediaRecorderRef.current = mediaRecorder;
    audioChunksRef.current = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      // Combine all chunks
      const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
      
      console.log(`Recording stopped. Size: ${audioBlob.size} bytes`);

      // Convert to base64
      const reader = new FileReader();
      reader.readAsDataURL(audioBlob);
      reader.onloadend = () => {
        const base64Audio = reader.result.split(',')[1];
        
        // Send complete audio file
        sendMessage({
          type: 'audio_complete',
          audio: base64Audio,
          mimeType: mimeType,
          size: audioBlob.size
        });
      };

      // Stop tracks
      stream.getTracks().forEach((track) => track.stop());
    };

    // Start recording (collect data every 1 second)
    mediaRecorder.start(1000);
    setIsRecording(true);
    
    console.log('Recording started...');
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

  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.9;
      utterance.pitch = 1;
      utterance.volume = 1;
      
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
    <>
      <Navbar />
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        {/* Header */}
        <div className="bg-white shadow-sm">
          <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <button
                  onClick={() => navigate('/dashboard')}
                  className="p-2 hover:bg-gray-100 rounded-lg transition"
                >
                  <ArrowLeft className="w-5 h-5 text-gray-600" />
                </button>
                <div className="bg-blue-600 p-2 rounded-lg">
                  <Activity className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">
                    AI Therapy Session
                  </h1>
                  <p className="text-sm text-gray-500">Session: {currentSessionId.slice(0, 16)}...</p>
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
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
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
        </div>
      </div>
    </>
  );
};