import { useRef, useEffect, useState } from 'react';
import Webcam from 'react-webcam';
import { Camera, CameraOff } from 'lucide-react';

export const VideoPanel = ({ onFrame, isConnected }) => {
  const webcamRef = useRef(null);
  const [isCameraOn, setIsCameraOn] = useState(true);
  const [currentEmotion, setCurrentEmotion] = useState(null);

  useEffect(() => {
    if (!isCameraOn || !isConnected) return;

    const interval = setInterval(() => {
      if (webcamRef.current) {
        const imageSrc = webcamRef.current.getScreenshot();
        if (imageSrc && onFrame) {
          onFrame(imageSrc);
        }
      }
    }, 500); // Send frame every 500ms

    return () => clearInterval(interval);
  }, [isCameraOn, isConnected, onFrame]);

  return (
    <div className="bg-white rounded-lg shadow-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-800 flex items-center space-x-2">
          <Camera className="w-5 h-5" />
          <span>Facial Analysis</span>
        </h3>
        <button
          onClick={() => setIsCameraOn(!isCameraOn)}
          className={`p-2 rounded-lg ${isCameraOn ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-600'}`}
        >
          {isCameraOn ? <CameraOff className="w-4 h-4" /> : <Camera className="w-4 h-4" />}
        </button>
      </div>

      <div className="relative bg-gray-900 rounded-lg overflow-hidden aspect-video">
        {isCameraOn ? (
          <Webcam
            ref={webcamRef}
            audio={false}
            screenshotFormat="image/jpeg"
            className="w-full h-full object-cover"
            videoConstraints={{
              width: 640,
              height: 480,
              facingMode: 'user',
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <CameraOff className="w-12 h-12" />
          </div>
        )}

        {currentEmotion && isCameraOn && (
          <div className="absolute bottom-4 left-4 bg-black bg-opacity-70 text-white px-4 py-2 rounded-lg">
            <p className="text-sm font-medium">
              {currentEmotion.emotion} ({(currentEmotion.confidence * 100).toFixed(0)}%)
            </p>
          </div>
        )}

        {!isConnected && (
          <div className="absolute top-4 right-4 bg-red-500 text-white px-3 py-1 rounded-full text-xs font-medium">
            Disconnected
          </div>
        )}
      </div>
    </div>
  );
};