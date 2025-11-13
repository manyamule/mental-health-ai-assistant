import { Smile, Frown, Meh, AlertCircle, Angry } from 'lucide-react';

const emotionIcons = {
  happy: Smile,
  happiness: Smile,
  sadness: Frown,
  neutral: Meh,
  fear: AlertCircle,
  anger: Angry,
  surprise: AlertCircle,
};

const emotionColors = {
  happy: 'text-green-600 bg-green-100',
  happiness: 'text-green-600 bg-green-100',
  sadness: 'text-blue-600 bg-blue-100',
  neutral: 'text-gray-600 bg-gray-100',
  fear: 'text-yellow-600 bg-yellow-100',
  anger: 'text-red-600 bg-red-100',
  surprise: 'text-purple-600 bg-purple-100',
};

export const EmotionDisplay = ({ facialEmotion, voiceEmotion, overallState }) => {
  const EmotionCard = ({ title, emotion, confidence }) => {
    const Icon = emotionIcons[emotion] || Meh;
    const colorClass = emotionColors[emotion] || 'text-gray-600 bg-gray-100';

    return (
      <div className="bg-white rounded-lg p-4 shadow">
        <p className="text-xs text-gray-500 mb-2">{title}</p>
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${colorClass}`}>
            <Icon className="w-6 h-6" />
          </div>
          <div>
            <p className="font-semibold capitalize">{emotion || 'None'}</p>
            {confidence && (
              <p className="text-sm text-gray-500">{(confidence * 100).toFixed(0)}%</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-4">
      <h3 className="font-semibold text-gray-800 mb-4">Emotion Analysis</h3>
      
      <div className="space-y-3">
        <EmotionCard
          title="Facial Expression"
          emotion={facialEmotion?.emotion}
          confidence={facialEmotion?.confidence}
        />
        
        <EmotionCard
          title="Voice Tone"
          emotion={voiceEmotion?.emotion}
          confidence={voiceEmotion?.confidence}
        />
        
        {overallState && (
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 mt-4">
            <p className="text-xs text-gray-600 mb-2">Overall Emotional State</p>
            <p className="font-semibold text-lg capitalize">{overallState.dominant_emotion}</p>
            <div className="mt-2 space-y-1">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Valence:</span>
                <span className={overallState.valence > 0 ? 'text-green-600' : 'text-red-600'}>
                  {overallState.valence > 0 ? 'Positive' : 'Negative'}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Arousal:</span>
                <span className={overallState.arousal > 0 ? 'text-orange-600' : 'text-blue-600'}>
                  {overallState.arousal > 0 ? 'High Energy' : 'Low Energy'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};