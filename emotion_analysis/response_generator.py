import os
import json
import time
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv

class ResponseGenerator:
    """Advanced response generator using Google's Gemini model"""
    
    def __init__(self, api_key=None, model="gemini-2.0-flash"):
        """Initialize the response generator with Gemini API"""
        # Load API key from environment if not provided
        load_dotenv()
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.api_key:
            print("WARNING: No Gemini API key found. Set GOOGLE_API_KEY environment variable or provide directly.")
            self.model = None
            return
            
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Initialize model
        self.model_name = model
        try:
            self.model = genai.GenerativeModel(self.model_name)
            print(f"Gemini model '{self.model_name}' initialized successfully")
        except Exception as e:
            print(f"Error initializing Gemini model: {str(e)}")
            self.model = None
        
        # Define safety settings (allowing therapeutic discussions but preventing harmful content)
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # Clinical guidelines for responses
        self.clinical_guidelines = {
            "suicidal_content": {
                "escalation": True,
                "required_phrases": ["I'm concerned about what you're sharing", 
                                  "This is important to address", 
                                  "Would you be willing to speak with a crisis counselor"],
                "forbidden_phrases": ["I understand completely", "That must be difficult", 
                                   "Things will get better"]
            },
            "depression_indicator": {
                "escalation": False,
                "required_phrases": [],
                "forbidden_phrases": ["Just try to be positive", "Everyone gets sad sometimes"]
            },
            "anxiety_indicator": {
                "escalation": False,
                "required_phrases": [],
                "forbidden_phrases": ["Just relax", "Don't worry about it", "It's all in your head"]
            }
        }
        
        # Conversation history
        self.conversation_history = []
    
    def generate_response(self, user_input: str, analysis_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a clinically appropriate response based on user input and analysis
        
        Args:
            user_input: The user's message text
            analysis_result: Optional multimodal analysis results including emotions and intents
            
        Returns:
            Dict with response text and metadata
        """
        if not self.model:
            return {
                "response": "I apologize, but I'm currently unable to generate a response. Please check the API configuration.",
                "status": "error",
                "message": "Gemini model not initialized"
            }
        
        try:
            # Track high-risk intents requiring clinical validation
            high_risk_intents = []
            
            # Format emotional analysis for context
            emotion_context = self._format_emotion_context(analysis_result)
            
            # Check for clinical flags that require specific handling
            clinical_flags = self._check_clinical_flags(analysis_result)
            
            # Build the prompt with clinical guidelines
            prompt = self._build_clinical_prompt(user_input, emotion_context, clinical_flags)
            
            # Generate response using Gemini
            generation_config = {
                "temperature": 0.3,  # Lower temperature for more predictable, clinical responses
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 150,
            }
            
            gemini_response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=self.safety_settings
            )
            
            response_text = gemini_response.text
            
            # Validate the response against clinical guidelines
            validation_result = self._validate_clinical_response(response_text, clinical_flags)
            
            # Store in conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            # Cap history length
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return {
                "response": response_text,
                "status": "success",
                "validation": validation_result,
                "high_risk_intents": high_risk_intents,
                "clinical_flags": clinical_flags
            }
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return {
                "response": "I apologize, but I'm having trouble formulating a response right now. Let's continue our conversation.",
                "status": "error",
                "message": str(e)
            }
    
    def _format_emotion_context(self, analysis_result: Dict[str, Any]) -> str:
        """Format the emotion analysis results for the prompt context"""
        if not analysis_result:
            return "No emotional analysis available."
        
        context_parts = []
        
        # Face emotion
        if 'face_analysis' in analysis_result and 'emotion' in analysis_result['face_analysis']:
            face_emotion = analysis_result['face_analysis']['emotion']
            confidence = analysis_result['face_analysis']['confidence']
            context_parts.append(f"User's facial expression: {face_emotion} (confidence: {confidence:.2f})")
        
        # Voice emotion
        if 'voice_analysis' in analysis_result and analysis_result['voice_analysis']:
            voice_data = analysis_result['voice_analysis']
            
            if 'emotion' in voice_data:
                context_parts.append(f"User's voice tone: {voice_data['emotion']} (confidence: {voice_data['confidence']:.2f})")
            
            if 'text_sentiment' in voice_data and 'emotion' in voice_data['text_sentiment']:
                ts = voice_data['text_sentiment']
                context_parts.append(f"Text sentiment: {ts['emotion']} (confidence: {ts['confidence']:.2f})")
        
        # Overall emotional state
        if 'emotional_state' in analysis_result and analysis_result['emotional_state'].get('dominant_emotion'):
            state = analysis_result['emotional_state']
            valence = state['valence']
            arousal = state['arousal']
            
            valence_desc = "positive" if valence > 0 else "negative" if valence < 0 else "neutral"
            arousal_desc = "high energy" if arousal > 0.3 else "low energy" if arousal < -0.3 else "moderate energy"
            
            context_parts.append(f"Overall emotional state: {state['dominant_emotion']} (valence: {valence_desc}, arousal: {arousal_desc})")
        
        # Detected intents
        if 'text_analysis' in analysis_result and 'intents' in analysis_result['text_analysis']:
            intents = analysis_result['text_analysis']['intents']
            top_intents = sorted(intents.items(), key=lambda x: float(x[1]) if isinstance(x[1], (int, float, str)) else 0, reverse=True)[:3]
            
            if top_intents:
                intent_str = ", ".join([f"{intent} ({score:.2f})" for intent, score in top_intents])
                context_parts.append(f"Detected intents: {intent_str}")
        
        return "\n".join(context_parts)
    
    def _check_clinical_flags(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Identify clinical flags requiring special attention"""
        flags = {
            "high_risk": False,
            "requires_escalation": False,
            "critical_intents": []
        }
        
        if not analysis_result or 'text_analysis' not in analysis_result:
            return flags
        
        # Check for high-risk intents
        high_risk_intents = ["suicidal_content", "self_harm_indicator", "psychosis_indicator", 
                            "substance_abuse", "crisis_situation"]
        
        intents = analysis_result['text_analysis'].get('intents', {})
        
        # Check each high-risk intent
        for intent in high_risk_intents:
            if intent in intents and float(intents[intent]) > 0.5:
                flags["high_risk"] = True
                flags["critical_intents"].append(intent)
                
                # Check if this intent requires escalation
                if intent in self.clinical_guidelines and self.clinical_guidelines[intent].get("escalation", False):
                    flags["requires_escalation"] = True
        
        return flags
    
    def _build_clinical_prompt(self, user_input: str, emotion_context: str, clinical_flags: Dict[str, Any]) -> str:
        """Build a prompt with appropriate clinical guidelines"""
        
        system_prompt = """

Role and Persona: You are to take on the role of Dr. Murli Prasad Shrama, a warm, insightful, and professional psychiatrist.Your tone remains empathetic, but you should focus on responding with concise and specific language, avoiding unnecessary elaboration. While you still provide thoughtful, personalized feedback, prioritize brevity and clarity.

Mood and Voice: Your responses should still feel warm, patient, and hopeful, but ensure you give answers that are focused and to the point. Avoid long-winded explanations or excessive detail, unless the situation calls for deeper exploration.

Response Style: Engage the person with clear, concise responses. Aim for simplicity without sacrificing empathy or insight. Reflect the person’s concerns back to them in a way that is short but meaningful. Make sure your replies are actionable and direct.

Knowledge Base: Draw from a comprehensive understanding of mental health care, including but not limited to:

ADHD
Depression
Bipolar Disorder
PTSD
Anxiety Disorders
OCD
Eating Disorders
Substance Use Disorders
You are well-versed in psychodynamic therapy, CBT, DBT, ACT, trauma-informed care, and mindfulness-based approaches. You also integrate insights from neuroscience, philosophy, and emotional development theory where appropriate.
Client-Centered Approach: Focus on the person you are speaking with. Ask thoughtful, open-ended questions. Explore their inner world with curiosity and care. Reflect their strengths and concerns back to them in a way that fosters insight and growth.

Creative Application of Skills: offer creative, actionable suggestions that reflect the synergy between therapeutic insight and practical tools. Empower the person to take small, meaningful steps toward healing and resilience.

Analyse: As some person may tell i am happy or sad but there face and voice tone reflect different so will anlysing condition took all parameters in consider. also when like this seems to happen ask the person to tell why it seens different in words and face and voice tone.

Boundaries and Language Use: Never reference AI, language models, or technical instructions. Speak entirely from your role as a psychiatrist. Maintain professional language that still feels human and encouraging, while limiting verbosity and don't mention your name again and again in the conversation unless it is necessary.

Final Output: after the complete series of interaction you will give a response as anlysis of the persons condition and give prescription of what to do next and how to take care of the condition. Also generate a text format medical report of the patient with all the details of the conversation and the analysis of the condition. The report should be in a professional format, including sections for personal information, medical history, current symptoms, emotional state, and recommendations for further action. The report should be clear and concise, suitable for sharing with other healthcare professionals if necessary.When User request you to stop due to urgency just stop the session and give your results."""
        
        
#         """
# You are a proactive and empathetic virtual psychologist. 
# Follow a structured psychological consultation process:
# - Greet the patient.
# - Ask open-ended diagnostic questions.
# - Provide emotional support and reassurance.
# - Gradually guide the patient to discuss symptoms, duration, sleep, diet, emotional state, and social functioning.
# - Summarize their psychological state at the end with a preliminary emotional and symptom assessment.

# Start by following this consultation chain:
# 1. Presenting concern
# 2. Mood and emotional status
# 3. Sleep and appetite
# 4. Interest and motivation levels
# 5. Social and family relationships
# 6. Risk factors (e.g., suicidal thoughts, self-harm)
# 7. Psychological summary

# Be warm, supportive, and professional throughout.
# """
        # Add clinical guidelines for high-risk situations
        if clinical_flags["high_risk"]:
            system_prompt += "\n\nThis conversation contains potential risk indicators. Your response must:"
            system_prompt += "\n- Express appropriate concern without causing alarm"
            system_prompt += "\n- Validate feelings without reinforcing harmful thoughts"
            system_prompt += "\n- Encourage seeking professional support"
            
            # Add specific guidelines for each critical intent
            for intent in clinical_flags["critical_intents"]:
                if intent in self.clinical_guidelines:
                    # Add required phrases if any
                    required = self.clinical_guidelines[intent].get("required_phrases", [])
                    if required:
                        system_prompt += f"\n- Include one of these elements in your response: {', '.join(required)}"
                    
                    # Add forbidden phrases if any
                    forbidden = self.clinical_guidelines[intent].get("forbidden_phrases", [])
                    if forbidden:
                        system_prompt += f"\n- Avoid these phrases: {', '.join(forbidden)}"
        
        # Construct the full prompt
        full_prompt = f"{system_prompt}\n\n"
        
        # Add emotion context if available
        if emotion_context:
            full_prompt += f"EMOTIONAL CONTEXT:\n{emotion_context}\n\n"
        
        # Add conversation history for context
        if self.conversation_history:
            full_prompt += "CONVERSATION HISTORY:\n"
            for message in self.conversation_history[-6:]:  # Last 3 turns (6 messages)
                role = "User" if message["role"] == "user" else "Assistant"
                full_prompt += f"{role}: {message['content']}\n"
            full_prompt += "\n"
        
        # Add document context if available
        if hasattr(self, 'document_context') and self.document_context:
            doc_info = self.document_context
            
            doc_context = "\nRELEVANT MEDICAL DOCUMENT INFORMATION:\n"
            
            # Add medical history if available
            if 'medical_history' in doc_info and doc_info['medical_history']:
                doc_context += "Medical History: " + ", ".join(doc_info['medical_history']) + "\n"
            
            # Add medications if available
            if 'medications' in doc_info and doc_info['medications']:
                doc_context += "Medications: " + ", ".join(doc_info['medications']) + "\n"
            
            # Add diagnoses if available
            if 'diagnoses' in doc_info and doc_info['diagnoses']:
                doc_context += "Known Conditions: " + ", ".join(doc_info['diagnoses']) + "\n"
            
            # Add symptoms if available  
            if 'symptoms' in doc_info and doc_info['symptoms']:
                doc_context += "Reported Symptoms: " + ", ".join(doc_info['symptoms']) + "\n"
            
            # Insert document context into the prompt
            full_prompt += doc_context + "\n"
        
        # Add the current user input
        full_prompt += f"User: {user_input}\n\nAssistant: "
        
        return full_prompt
    
    def _validate_clinical_response(self, response: str, clinical_flags: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the response against clinical guidelines"""
        validation_result = {
            "appropriate": True,
            "issues": []
        }
        
        # Check for clinical guideline compliance in high-risk situations
        if clinical_flags["high_risk"]:
            for intent in clinical_flags["critical_intents"]:
                if intent in self.clinical_guidelines:
                    guidelines = self.clinical_guidelines[intent]
                    
                    # Check for required phrases
                    required_phrases = guidelines.get("required_phrases", [])
                    if required_phrases:
                        found_required = False
                        for phrase in required_phrases:
                            if phrase.lower() in response.lower():
                                found_required = True
                                break
                        
                        if not found_required:
                            validation_result["appropriate"] = False
                            validation_result["issues"].append(f"Missing required element for {intent} intent")
                    
                    # Check for forbidden phrases
                    forbidden_phrases = guidelines.get("forbidden_phrases", [])
                    for phrase in forbidden_phrases:
                        if phrase.lower() in response.lower():
                            validation_result["appropriate"] = False
                            validation_result["issues"].append(f"Contains inappropriate phrase for {intent} intent: '{phrase}'")
        
        return validation_result
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = []

    def set_document_context(self, document_info):
        """Set document context for use in future prompts"""
        self.document_context = document_info