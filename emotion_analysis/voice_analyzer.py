import numpy as np
import pyaudio
import wave
import threading
import time
import os
import librosa
import librosa.display
import matplotlib.pyplot as plt
import speech_recognition as sr
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import matplotlib
matplotlib.use('Agg')  # Use a non-GUI backend

class VoiceAnalyzer:
    def __init__(self):
        """
        Initialize the voice tone analyzer with speech-to-text and sentiment analysis
        """
        self.audio = None
        self.stream = None
        self.recording = False
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paInt16
        self.record_seconds = 5
        self.temp_dir = "temp_audio"
        self.latest_recording = None
        
        # Emotion mappings
        self.emotions = ["anger", "happiness", "sadness", "fear", "neutral"]
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        
        # Download NLTK resources if needed
        try:
            nltk.data.find('vader_lexicon')
        except LookupError:
            print("Downloading NLTK resources...")
            nltk.download('vader_lexicon')
        
        # Initialize sentiment analyzer
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Create temp directory if it doesn't exist
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
            
        print("Voice analyzer initialized with speech-to-text and sentiment analysis")
    
    def start_recording(self, duration=5):
        """Start recording audio in a separate thread"""
        if self.recording:
            print("Already recording")
            return False
            
        self.record_seconds = duration
        threading.Thread(target=self._record_audio).start()
        return True
    
    def _record_audio(self):
        """Record audio from microphone"""
        self.recording = True
        self.audio = pyaudio.PyAudio()
        
        # Create unique filename based on timestamp
        filename = os.path.join(self.temp_dir, f"recording_{int(time.time())}.wav")
        self.latest_recording = filename
        
        # Open stream
        stream = self.audio.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        print("Recording voice...")
        
        frames = []
        for i in range(0, int(self.sample_rate / self.chunk_size * self.record_seconds)):
            data = stream.read(self.chunk_size)
            frames.append(data)
            
        print("Recording finished")
        
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        self.audio.terminate()
        
        # Save the recording
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        self.recording = False
        
        return filename
    
    def is_recording(self):
        """Check if currently recording"""
        return self.recording
    
    def transcribe_audio(self, audio_file):
        """Convert speech to text using Google's speech recognition"""
        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data)
                return text
        except sr.UnknownValueError:
            print("Speech Recognition could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"Could not request results from Speech Recognition service; {e}")
            return ""
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return ""
    
    def analyze_text_sentiment(self, text):
        """Analyze sentiment of text using VADER"""
        if not text:
            return {
                "compound": 0,
                "pos": 0,
                "neg": 0,
                "neu": 0,
                "emotion": "neutral",
                "confidence": 0.5
            }
        
        sentiment = self.sentiment_analyzer.polarity_scores(text)
        
        # Map compound score to emotion
        compound = sentiment['compound']
        
        if compound >= 0.5:
            emotion = "happiness"
            confidence = min(0.5 + compound/2, 0.95)  # Scale 0.5-0.95
        elif compound <= -0.5:
            # Determine if it's anger or sadness based on text content
            anger_words = ['angry', 'mad', 'furious', 'annoyed', 'irritated', 'hate']
            fear_words = ['scared', 'afraid', 'terrified', 'anxious', 'nervous', 'worried', 'fear']
            
            text_lower = text.lower()
            
            if any(word in text_lower for word in anger_words):
                emotion = "anger"
            elif any(word in text_lower for word in fear_words):
                emotion = "fear"
            else:
                emotion = "sadness"
                
            confidence = min(0.5 + abs(compound)/2, 0.95)  # Scale 0.5-0.95
        elif -0.5 < compound < 0.5:
            emotion = "neutral"
            confidence = 0.5 + (0.5 - abs(compound))/2  # Higher confidence toward 0
        
        sentiment["emotion"] = emotion
        sentiment["confidence"] = confidence
        
        return sentiment
    
    def extract_features(self, file_path):
        """Extract comprehensive audio features for emotion analysis"""
        try:
            # Load audio file
            y, sr = librosa.load(file_path, sr=None)
            
            # Basic features
            # 1. Average energy (volume)
            energy = np.mean(librosa.feature.rms(y=y))
            
            # 2. Zero Crossing Rate - related to perceived noisiness
            zcr = np.mean(librosa.feature.zero_crossing_rate(y))
            
            # 3. Spectral Centroid - brightness of sound
            spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
            
            # 4. Spectral Rolloff - frequency below which most energy is contained
            rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
            
            # 5. Spectral Bandwidth - width of frequency band
            bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))
            
            # 6. Tempo (BPM) - speed of speech
            onset_env = librosa.onset.onset_strength(y=y, sr=sr)
            tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=sr)[0]
            
            # 7. MFCCs - voice characteristics
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            mfcc_means = np.mean(mfccs, axis=1)
            mfcc_vars = np.var(mfccs, axis=1)
            
            # 8. Spectral Contrast - voice harmonics vs noise
            contrast = np.mean(librosa.feature.spectral_contrast(y=y, sr=sr), axis=1)
            
            # 9. Chroma - harmonic content
            chroma = np.mean(librosa.feature.chroma_stft(y=y, sr=sr), axis=1)
            
            # 10. Spectral Flux - rate of change of spectrum
            spec = np.abs(librosa.stft(y))
            spec_flux = np.mean(np.diff(spec, axis=1))
            
            # 11. Speech Rate (approximation)
            envelope = np.abs(y)
            threshold = 0.01
            speech_segments = np.where(envelope > threshold)[0]
            speech_rate = len(speech_segments) / (len(y) / sr) if len(y) > 0 else 0
            
            # 12. Pitch variation (fundamental frequency variation)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:  # Filter out zero pitches
                    pitch_values.append(pitch)
            
            pitch_mean = np.mean(pitch_values) if pitch_values else 0
            pitch_std = np.std(pitch_values) if pitch_values else 0
            
            # Combine all features
            features = {
                'energy': float(energy),
                'zero_crossing_rate': float(zcr),
                'spectral_centroid': float(spectral_centroid),
                'spectral_rolloff': float(rolloff),
                'spectral_bandwidth': float(bandwidth),
                'tempo': float(tempo),
                'speech_rate': float(speech_rate),
                'pitch_mean': float(pitch_mean),
                'pitch_std': float(pitch_std),
                'spectral_flux': float(spec_flux)
            }
            
            # Add MFCCs
            for i, val in enumerate(mfcc_means):
                features[f'mfcc{i+1}_mean'] = float(val)
            
            # Add spectral contrast
            for i, val in enumerate(contrast):
                features[f'contrast{i+1}'] = float(val)
            
            # Add chroma features
            for i, val in enumerate(chroma):
                features[f'chroma{i+1}'] = float(val)
                
            return features
            
        except Exception as e:
            print(f"Error extracting features: {str(e)}")
            return {}
    
    def analyze_acoustic_emotion(self, features):
        """Analyze emotional tone from acoustic features"""
        try:
            # Advanced rule-based classification
            # These rules are based on research on acoustic correlates of emotions
            
            # Extract key features
            energy = features['energy']
            zcr = features['zero_crossing_rate']
            pitch_mean = features['pitch_mean']
            pitch_std = features['pitch_std']
            speech_rate = features['speech_rate']
            spectral_centroid = features['spectral_centroid']
            
            # Emotion scores
            emotion_scores = {
                'anger': 0.0,
                'happiness': 0.0,
                'sadness': 0.0, 
                'fear': 0.0,
                'neutral': 0.3  # Baseline for neutral
            }
            
            # Anger indicators: high energy, high pitch, fast speech rate
            if energy > 0.05:
                emotion_scores['anger'] += 0.3
            if pitch_mean > 200:
                emotion_scores['anger'] += 0.2
            if speech_rate > 3.5:
                emotion_scores['anger'] += 0.2
            if spectral_centroid > 2000:
                emotion_scores['anger'] += 0.2
                
            # Happiness indicators: high energy, high pitch variation, medium-high speech rate
            if energy > 0.04:
                emotion_scores['happiness'] += 0.2
            if pitch_std > 40:
                emotion_scores['happiness'] += 0.3
            if speech_rate > 3.0 and speech_rate < 3.5:
                emotion_scores['happiness'] += 0.2
            if 1500 < spectral_centroid < 2000:
                emotion_scores['happiness'] += 0.2
                
            # Sadness indicators: low energy, low pitch, slow speech rate
            if energy < 0.03:
                emotion_scores['sadness'] += 0.3
            if pitch_mean < 180:
                emotion_scores['sadness'] += 0.2
            if speech_rate < 2.5:
                emotion_scores['sadness'] += 0.2
            if spectral_centroid < 1500:
                emotion_scores['sadness'] += 0.2
                
            # Fear indicators: variable energy, high pitch variation, irregular tempo
            if 0.02 < energy < 0.04:
                emotion_scores['fear'] += 0.2
            if pitch_std > 30:
                emotion_scores['fear'] += 0.2
            if features['tempo'] > 120:
                emotion_scores['fear'] += 0.2
            if zcr > 0.1:
                emotion_scores['fear'] += 0.2
                
            # Neutral is already given a baseline, reduce if other emotions have clear signals
            max_other_score = max(emotion_scores['anger'], emotion_scores['happiness'], 
                                  emotion_scores['sadness'], emotion_scores['fear'])
            if max_other_score > 0.5:
                emotion_scores['neutral'] -= min(0.2, max_other_score - 0.5)
                
            # Normalize scores to sum to 1
            total_score = sum(emotion_scores.values())
            if total_score > 0:
                for emotion in emotion_scores:
                    emotion_scores[emotion] = emotion_scores[emotion] / total_score
            
            # Find the dominant emotion
            dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])
            
            return {
                "emotion": dominant_emotion[0],
                "confidence": dominant_emotion[1],
                "all_emotions": emotion_scores
            }
                
        except Exception as e:
            print(f"Error during acoustic emotion analysis: {str(e)}")
            return {
                "emotion": "neutral", 
                "confidence": 0.5,
                "all_emotions": {"neutral": 1.0}
            }
    
    def analyze_emotion(self, audio_file=None):
        """
        Analyze emotional tone using both acoustic features and text sentiment
        with higher weight given to text sentiment analysis
        """
        file_to_analyze = audio_file or self.latest_recording
        
        if not file_to_analyze or not os.path.exists(file_to_analyze):
            return {"status": "error", "message": "No valid audio file to analyze"}
        
        try:
            # Extract features for acoustic analysis
            features = self.extract_features(file_to_analyze)
            
            if not features:
                return {"status": "error", "message": "Failed to extract audio features"}
            
            # Create visualizations for audio analysis
            self._create_audio_visualization(file_to_analyze)
            
            # Convert speech to text
            transcribed_text = self.transcribe_audio(file_to_analyze)
            
            # Analyze text sentiment
            text_sentiment = self.analyze_text_sentiment(transcribed_text)
            
            # Analyze acoustic emotion
            acoustic_emotion = self.analyze_acoustic_emotion(features)
            
            # Weighted combination of text sentiment and acoustic emotion
            # Giving more weight to text sentiment (0.7) than acoustic emotion (0.3)
            text_weight = 0.7
            acoustic_weight = 0.3
            
            # Initialize combined emotion scores
            combined_emotions = {
                'anger': 0.0,
                'happiness': 0.0,
                'sadness': 0.0,
                'fear': 0.0,
                'neutral': 0.0
            }
            
            # Add weighted acoustic emotions
            for emotion, score in acoustic_emotion['all_emotions'].items():
                if emotion in combined_emotions:
                    combined_emotions[emotion] += score * acoustic_weight
            
            # Add weighted text sentiment
            text_emotion = text_sentiment['emotion']
            text_confidence = text_sentiment['confidence']
            
            if text_emotion in combined_emotions:
                combined_emotions[text_emotion] += text_confidence * text_weight
            
            # Find the dominant emotion
            dominant_emotion, confidence = max(combined_emotions.items(), key=lambda x: x[1])
            
            # Normalize combined scores
            total = sum(combined_emotions.values())
            if total > 0:
                for emotion in combined_emotions:
                    combined_emotions[emotion] /= total
            
            return {
                "emotion": dominant_emotion,
                "confidence": confidence,
                "transcribed_text": transcribed_text,
                "text_sentiment": text_sentiment,
                "acoustic_emotion": acoustic_emotion,
                "all_emotions": combined_emotions,
                "features": features,
                "audio_file": file_to_analyze
            }
                
        except Exception as e:
            print(f"Error during voice analysis: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _create_audio_visualization(self, file_path):
        """Create visualizations of the audio for analysis"""
        try:
            # Create a subdirectory for visualizations
            vis_dir = os.path.join(self.temp_dir, "visualizations")
            if not os.path.exists(vis_dir):
                os.makedirs(vis_dir)
                
            # Base filename for visualizations
            base_name = os.path.basename(file_path).split('.')[0]
            
            # Load audio
            y, sr = librosa.load(file_path, sr=None)
            
            # 1. Waveform
            plt.figure(figsize=(10, 4))
            librosa.display.waveshow(y, sr=sr)
            plt.title('Waveform')
            plt.tight_layout()
            plt.savefig(os.path.join(vis_dir, f"{base_name}_waveform.png"))
            plt.close()
            
            # 2. Spectrogram
            plt.figure(figsize=(10, 4))
            D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)
            librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='log')
            plt.colorbar(format='%+2.0f dB')
            plt.title('Spectrogram')
            plt.tight_layout()
            plt.savefig(os.path.join(vis_dir, f"{base_name}_spectrogram.png"))
            plt.close()
            
            # 3. MFCCs
            plt.figure(figsize=(10, 4))
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            librosa.display.specshow(mfccs, sr=sr, x_axis='time')
            plt.colorbar()
            plt.title('MFCCs')
            plt.tight_layout()
            plt.savefig(os.path.join(vis_dir, f"{base_name}_mfccs.png"))
            plt.close()
            
            print(f"Visualizations saved to {vis_dir}")
            
        except Exception as e:
            print(f"Error creating visualizations: {str(e)}")
    
    def cleanup(self):
        """Remove temporary audio files"""
        for file in os.listdir(self.temp_dir):
            if file.endswith(".wav"):
                try:
                    os.remove(os.path.join(self.temp_dir, file))
                except:
                    pass