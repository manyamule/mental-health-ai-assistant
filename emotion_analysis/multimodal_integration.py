import numpy as np
import sys
import os

# Add parent directory to path to import from other modules

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intent_classification.intent_classifier import IntentClassifier
from emotion_analysis.voice_analyzer import VoiceAnalyzer
from emotion_analysis.response_generator import ResponseGenerator

class MultimodalAnalyzer:
    def __init__(self, emotion_analyzer=None, intent_classifier=None, voice_analyzer=None):
        """Initialize the multimodal analyzer"""
        self.emotion_analyzer = emotion_analyzer
        self.intent_classifier = intent_classifier
        self.voice_analyzer = voice_analyzer
        self.response_generator = ResponseGenerator()  # Add response generator
        self.session_emotions = []
        self.session_voice_emotions = []
        self.session_intents = []
        self.emotion_weights = {
            'surprise': {'valence': 0.1, 'arousal': 0.8},
            'happy': {'valence': 0.9, 'arousal': 0.6},
            'happiness': {'valence': 0.9, 'arousal': 0.6},
            'anger': {'valence': -0.8, 'arousal': 0.9},
            'sadness': {'valence': -0.7, 'arousal': -0.4},
            'fear': {'valence': -0.8, 'arousal': 0.7},
            'neutral': {'valence': 0.0, 'arousal': 0.0}
        }
        
    def analyze_response(self, text, face_image=None, voice_file=None):
        """Perform multimodal analysis of text, facial expression, and voice"""
        # Get text-based intents
        text_analysis = {}
        if self.intent_classifier:
            try:
                text_analysis = self.intent_classifier.analyze_response(text)
                self.session_intents.append(text_analysis)
            except Exception as e:
                print(f"Error analyzing text: {e}")
                # Create a basic text analysis if intent classification fails
                text_analysis = {
                    'text': text,
                    'intents': {'error': 'Models not loaded'},
                    'entities': {},
                    'suggested_followups': [
                        {
                            'priority': 'low',
                            'type': 'general_exploration',
                            'text': 'Could you tell me more about how you\'ve been feeling lately?'
                        }
                    ]
                }
        
        # Get emotion from face
        face_analysis = {}
        if self.emotion_analyzer and face_image is not None:
            self.emotion_analyzer.add_frame(face_image)
            if len(self.emotion_analyzer.frame_buffer) >= 3:
                face_analysis = self.emotion_analyzer.get_emotion()
                
                # Store emotion data if valid
                if 'emotion' in face_analysis:
                    self.session_emotions.append(face_analysis)
        
        # Get emotion from voice
        voice_analysis = {}
        if self.voice_analyzer and voice_file:
            voice_analysis = self.voice_analyzer.analyze_emotion(voice_file)
            if 'emotion' in voice_analysis:
                self.session_voice_emotions.append(voice_analysis)
        
        # Integrate all analyses
        integrated_analysis = self._integrate_analyses(text_analysis, face_analysis, voice_analysis)
        
        return integrated_analysis
    
    def _integrate_analyses(self, text_analysis, face_analysis, voice_analysis=None):
        """Integrate text, facial and voice analyses to form a complete understanding"""
        result = {
            'text_analysis': text_analysis,
            'face_analysis': face_analysis,
            'voice_analysis': voice_analysis,
            'emotional_state': self._estimate_emotional_state(),
            'clinical_relevance': text_analysis.get('clinical_relevance', {})
        }
        
        # Merge suggested followups, prioritizing high-risk ones
        text_followups = text_analysis.get('suggested_followups', [])
        emotion_followups = self._generate_emotion_followups(face_analysis, voice_analysis)
        
        # Start with high priority followups
        high_priority = [f for f in text_followups if f.get('priority') == 'high']
        
        # Add medium priority that aren't redundant
        medium_priority = [f for f in text_followups + emotion_followups 
                          if f.get('priority') == 'medium' and 
                          f.get('type') not in [h.get('type') for h in high_priority]]
        
        # Add remaining low priority
        low_priority = [f for f in text_followups + emotion_followups 
                       if f.get('priority') == 'low' and 
                       f.get('type') not in [h.get('type') for h in high_priority + medium_priority]]
        
        # Combine followups in priority order
        result['suggested_followups'] = high_priority + medium_priority + low_priority
        
        return result
    
    def _estimate_emotional_state(self):
        """Estimate overall emotional state from session data"""
        if not self.session_emotions and not self.session_voice_emotions:
            return {'valence': 0, 'arousal': 0, 'dominant_emotion': None}
        
        # Get recent emotions (last 10)
        recent_emotions = self.session_emotions[-10:] if self.session_emotions else []
        recent_voice_emotions = self.session_voice_emotions[-10:] if self.session_voice_emotions else []
        
        # Count emotion occurrences with weights (face 0.6, voice 0.4)
        emotion_counts = {}
        for entry in recent_emotions:
            emotion = entry.get('emotion')
            if emotion:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 0.6
                
        for entry in recent_voice_emotions:
            emotion = entry.get('emotion')
            if emotion:
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 0.4
        
        # Find dominant emotion
        dominant_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else None
        
        # Calculate average valence and arousal
        valence_sum = 0
        arousal_sum = 0
        count = 0
        
        for entry in recent_emotions:
            emotion = entry.get('emotion')
            if emotion and emotion in self.emotion_weights:
                valence_sum += self.emotion_weights[emotion]['valence'] * 0.6
                arousal_sum += self.emotion_weights[emotion]['arousal'] * 0.6
                count += 0.6
        
        for entry in recent_voice_emotions:
            emotion = entry.get('emotion')
            if emotion and emotion in self.emotion_weights:
                valence_sum += self.emotion_weights[emotion]['valence'] * 0.4
                arousal_sum += self.emotion_weights[emotion]['arousal'] * 0.4
                count += 0.4
        
        valence = valence_sum / count if count > 0 else 0
        arousal = arousal_sum / count if count > 0 else 0
        
        return {
            'valence': valence,  # -1 (negative) to 1 (positive)
            'arousal': arousal,  # -1 (low energy) to 1 (high energy)
            'dominant_emotion': dominant_emotion,
            'emotion_distribution': emotion_counts
        }
    
    def _generate_emotion_followups(self, face_analysis, voice_analysis=None):
        """Generate follow-up questions based on facial and voice emotions"""
        followups = []
        
        # Process face emotions first
        if face_analysis and 'emotion' in face_analysis:
            emotion = face_analysis['emotion']
            confidence = face_analysis['confidence']
            
            # Only suggest followups for high-confidence emotions
            if confidence < 0.6:
                return followups
                
            # Emotion-specific followups
            if emotion == 'sadness' and confidence > 0.7:
                followups.append({
                    'priority': 'medium',
                    'type': 'emotion_exploration',
                    'text': 'I notice you seem sad. Would you like to talk about what\'s troubling you?'
                })
            elif emotion == 'fear' and confidence > 0.7:
                followups.append({
                    'priority': 'medium',
                    'type': 'emotion_exploration',
                    'text': 'You appear anxious. Is there something specific that\'s causing you to feel afraid?'
                })
            elif emotion == 'anger' and confidence > 0.7:
                followups.append({
                    'priority': 'medium',
                    'type': 'emotion_exploration',
                    'text': 'You seem frustrated. Can you tell me what\'s making you feel this way?'
                })
            elif emotion == 'surprise' and confidence > 0.7:
                followups.append({
                    'priority': 'low',
                    'type': 'emotion_exploration',
                    'text': 'You look surprised. Did something I said catch you off guard?'
                })
            
        # Now check voice emotions with enhanced processing
        if voice_analysis and 'emotion' in voice_analysis:
            emotion = voice_analysis['emotion']
            confidence = voice_analysis['confidence']
            transcribed_text = voice_analysis.get('transcribed_text', '')
            
            # Only suggest followups for high-confidence voice emotions
            if confidence < 0.65:
                return followups
                
            # Voice-specific followups with text awareness
            if emotion == 'sadness' and confidence > 0.7:
                if transcribed_text:
                    followups.append({
                        'priority': 'medium',
                        'type': 'voice_emotion_exploration',
                        'text': f'When you said "{transcribed_text}", you sounded sad. Would you like to talk more about that?'
                    })
                else:
                    followups.append({
                        'priority': 'medium',
                        'type': 'voice_emotion_exploration',
                        'text': 'I notice from your tone of voice that you might be feeling down. Would you like to talk about that?'
                    })
            elif emotion == 'anger' and confidence > 0.7:
                if transcribed_text:
                    followups.append({
                        'priority': 'medium',
                        'type': 'voice_emotion_exploration',
                        'text': f'I sense some frustration when you said "{transcribed_text}". What specifically is bothering you?'
                    })
                else:
                    followups.append({
                        'priority': 'medium',
                        'type': 'voice_emotion_exploration',
                        'text': 'Your voice suggests you might be frustrated or upset. Is there something specific bothering you?'
                    })
            # Add other emotion-specific followups with text awareness
            
        return followups
    
    def generate_response(self, text, analysis_result=None):
        """Generate a clinically appropriate response based on analysis"""
        if analysis_result is None:
            # If no analysis is provided, use the last input
            face_image = None
            if self.emotion_analyzer:
                face_image = self.emotion_analyzer.get_current_face()
            
            analysis_result = self.analyze_response(text, face_image)
        
        # Generate response using the LLM
        response_data = self.response_generator.generate_response(text, analysis_result)
        
        # Add response data to the analysis result
        analysis_result['generated_response'] = response_data
        
        return analysis_result
    
    def reset_session(self):
        """Reset the session data"""
        self.session_emotions = []
        self.session_voice_emotions = []
        self.session_intents = []
        
        if self.emotion_analyzer:
            self.emotion_analyzer.reset()