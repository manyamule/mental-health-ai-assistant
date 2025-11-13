import os
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.multiclass import OneVsRestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MultiLabelBinarizer
import joblib
import re
import string

class IntentClassifier:
    def __init__(self, model_dir="intent_models"):
        self.model_dir = model_dir
        self.vectorizer = None
        self.classifier = None
        self.label_encoder = None
        self.intents = {}
        self.entity_patterns = self._build_entity_patterns()
        
        # Create model directory if it doesn't exist
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
            
        # Try to load existing models
        self._load_models()
    
    def _build_entity_patterns(self):
        """Build regex patterns for entity extraction"""
        return {
            "time_period": re.compile(r'\b(days|weeks|months|years|daily|weekly|nightly)\b'),
            "severity": re.compile(r'\b(mild|moderate|severe|extreme|slightly|very|really|barely|hardly)\b'),
            "frequency": re.compile(r'\b(always|often|sometimes|rarely|never|occasionally|frequently)\b'),
            "symptoms": {
                "sleep": re.compile(r'\b(sleep|insomnia|nightmares|tired|exhausted|rest|nap|awake|wake|waking|trouble sleeping|asleep|bed)\b'),
                "mood": re.compile(r'\b(sad|happy|angry|upset|irritable|mood|feeling|depression|anxiety|worried|stress)\b'),
                "appetite": re.compile(r'\b(eat|eating|appetite|weight|food|hungry|meal|diet|nutrition)\b'),
                "energy": re.compile(r'\b(energy|tired|exhausted|fatigue|motivation|lethargy|activity|exercise)\b'),
                "concentration": re.compile(r'\b(focus|concentrate|attention|distract|memory|thinking|thoughts|mind|remember)\b'),
                "suicidal": re.compile(r'\b(suicidal|death|die|harm|hurt|life|living|end|worth|pointless|better off without|wasn\'t here)\b')
            }
        }
    
    def _load_models(self):
        """Load trained models if they exist"""
        try:
            if os.path.exists(f"{self.model_dir}/vectorizer.pkl"):
                self.vectorizer = joblib.load(f"{self.model_dir}/vectorizer.pkl")
            
            if os.path.exists(f"{self.model_dir}/classifier.pkl"):
                self.classifier = joblib.load(f"{self.model_dir}/classifier.pkl")
                
            if os.path.exists(f"{self.model_dir}/label_encoder.pkl"):
                self.label_encoder = joblib.load(f"{self.model_dir}/label_encoder.pkl")
                
            if os.path.exists(f"{self.model_dir}/intents.json"):
                with open(f"{self.model_dir}/intents.json", "r") as f:
                    self.intents = json.load(f)
                    
            return True
        except Exception as e:
            print(f"Error loading models: {str(e)}")
            return False
    
    def _save_models(self):
        """Save trained models"""
        try:
            joblib.dump(self.vectorizer, f"{self.model_dir}/vectorizer.pkl")
            joblib.dump(self.classifier, f"{self.model_dir}/classifier.pkl")
            joblib.dump(self.label_encoder, f"{self.model_dir}/label_encoder.pkl")
            
            with open(f"{self.model_dir}/intents.json", "w") as f:
                json.dump(self.intents, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving models: {str(e)}")
            return False
    
    def _preprocess_text(self, text):
        """Clean text for processing"""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def train(self, training_data):
        """
        Train the intent classifier
        training_data: list of dict with 'text' and 'intents' keys
        """
        texts = [self._preprocess_text(item['text']) for item in training_data]
        intent_lists = [item['intents'] for item in training_data]
        
        # Save intents dictionary
        for item in training_data:
            for intent in item['intents']:
                if intent not in self.intents:
                    self.intents[intent] = {'description': f"Intent: {intent}", 'examples': []}
                if item['text'] not in self.intents[intent]['examples']:
                    self.intents[intent]['examples'].append(item['text'])
        
        # Create TF-IDF features with better parameters
        self.vectorizer = TfidfVectorizer(
            max_features=5000, 
            ngram_range=(1, 3),  # Include bigrams and trigrams
            min_df=2,            # Minimum document frequency
            use_idf=True
        )
        X = self.vectorizer.fit_transform(texts)
        
        # Encode labels
        self.label_encoder = MultiLabelBinarizer()
        y = self.label_encoder.fit_transform(intent_lists)
        
        # Train classifier with better parameters
        self.classifier = OneVsRestClassifier(
            LogisticRegression(
                C=1.0,              # Regularization strength
                class_weight='balanced',  # Handle class imbalance
                max_iter=200,       # More iterations for convergence
                solver='liblinear'  # Better for small datasets
            )
        )
        self.classifier.fit(X, y)
        
        # Save models
        return self._save_models()
    
    def predict(self, text, threshold=0.3):
        """
        Predict intents for a given text
        Returns dict with intents and confidence scores
        """
        if not self.classifier or not self.vectorizer or not self.label_encoder:
            return {"error": "Models not loaded"}
            
        # Clean text
        cleaned_text = self._preprocess_text(text)
        
        # Create features
        X = self.vectorizer.transform([cleaned_text])
        
        # Get prediction probabilities
        y_proba = self.classifier.predict_proba(X)
        
        # Get intent labels
        intent_labels = self.label_encoder.classes_
        
        # Create results - use higher threshold for sensitive intents
        results = {}
        for i, label in enumerate(intent_labels):
            score = y_proba[0][i]
            if label == "suicidal_content" and score >= 0.6:  # Higher threshold for suicide
                results[label] = float(score)
            elif score >= threshold:
                results[label] = float(score)
        
        # Sort by confidence
        results = {k: v for k, v in sorted(results.items(), key=lambda item: item[1], reverse=True)}
        
        # Limit to top 5 intents to reduce noise
        top_intents = dict(list(results.items())[:5])
        
        return top_intents
    
    def extract_entities(self, text):
        """Extract clinical entities from text"""
        entities = {}
        
        # Check for time periods
        time_periods = self.entity_patterns["time_period"].findall(text.lower())
        if time_periods:
            entities["time_period"] = time_periods
            
        # Check for severity indicators
        severity = self.entity_patterns["severity"].findall(text.lower())
        if severity:
            entities["severity"] = severity
            
        # Check for frequency indicators
        frequency = self.entity_patterns["frequency"].findall(text.lower())
        if frequency:
            entities["frequency"] = frequency
        
        # Check for symptoms
        entities["symptoms"] = []
        for symptom, pattern in self.entity_patterns["symptoms"].items():
            matches = pattern.findall(text.lower())
            if matches:
                entities["symptoms"].append({"type": symptom, "mentions": matches})
        
        return entities
    
    def analyze_response(self, text, context=None):
        """
        Full analysis of patient response
        Returns intents, entities, and suggested follow-up
        """
        # Get intent prediction
        intents = self.predict(text)
        
        # Extract entities
        entities = self.extract_entities(text)
        
        # Check for suicide risk
        suicide_risk = self._check_suicide_risk(text)
        if suicide_risk and "suicidal_content" not in intents:
            intents["suicidal_content"] = 0.85  # Force high confidence
        
        # Create analysis result
        analysis = {
            "text": text,
            "intents": intents,
            "entities": entities,
            "clinical_relevance": self._assess_clinical_relevance(intents, entities),
            "suicide_risk_detected": suicide_risk
        }
        
        # Generate follow-up suggestions based on analysis
        analysis["suggested_followups"] = self._suggest_followups(analysis, context)
        
        return analysis
    
    def _assess_clinical_relevance(self, intents, entities):
        """Assess clinical relevance of the response"""
        relevance = {"score": 0, "factors": []}
        
        # Check for specific intents that indicate clinical relevance
        clinical_intents = ["symptom_report", "emotional_distress", "treatment_discussion", 
                            "medication_mention", "side_effect_report", "suicidal_content"]
        
        for intent in clinical_intents:
            if intent in intents:
                relevance["score"] += intents[intent] * 0.5
                relevance["factors"].append(f"Intent: {intent}")
        
        # Check for symptom mentions
        if "symptoms" in entities and entities["symptoms"]:
            relevance["score"] += min(len(entities["symptoms"]) * 0.2, 0.6)
            relevance["factors"].append(f"Symptom mentions: {len(entities['symptoms'])}")
            
            # Higher relevance for suicidal content
            for symptom in entities["symptoms"]:
                if symptom["type"] == "suicidal":
                    relevance["score"] += 0.5
                    relevance["factors"].append("Suicide-related content")
        
        # Normalize score
        relevance["score"] = min(relevance["score"], 1.0)
        
        return relevance
    
    def _suggest_followups(self, analysis, context=None):
        """Generate follow-up question suggestions based on analysis"""
        followups = []
        
        # Handle possible suicidal content as highest priority
        suicide_indicators = analysis.get("suicide_risk_detected", False)
        
        # Only suggest suicide risk assessment if we have strong indicators
        if (suicide_indicators or 
            ("suicidal_content" in analysis["intents"] and analysis["intents"]["suicidal_content"] > 0.6)):
            followups.append({
                "priority": "high",
                "type": "risk_assessment",
                "text": "I notice you mentioned something that makes me concerned about your safety. Are you having thoughts of harming yourself?"
            })
        
        # Follow up on symptoms mentioned
        symptom_types = [s["type"] for s in analysis["entities"].get("symptoms", [])]
        
        if "sleep" in symptom_types and not suicide_indicators:
            followups.append({
                "priority": "medium",
                "type": "symptom_exploration",
                "text": "Can you tell me more about the sleep issues you're experiencing? How has this affected your daily life?"
            })
            
        if "mood" in symptom_types and not suicide_indicators:
            followups.append({
                "priority": "medium",
                "type": "symptom_exploration",
                "text": "You mentioned something about your mood. Could you describe how your mood has been over the past two weeks?"
            })
            
        if "appetite" in symptom_types and not suicide_indicators:
            followups.append({
                "priority": "medium",
                "type": "symptom_exploration",
                "text": "I'd like to understand more about the changes in your appetite or eating habits. Could you elaborate on that?"
            })
        
        # Follow up on medication mentions if detected
        if "medication_mention" in analysis["intents"] and analysis["intents"]["medication_mention"] > 0.5:
            followups.append({
                "priority": "medium",
                "type": "medication_exploration",
                "text": "You mentioned something about medication. Could you tell me more about your experience with it?"
            })
        
        # Generic follow-up if nothing specific was detected
        if len(followups) == 0:
            followups.append({
                "priority": "low",
                "type": "general_exploration",
                "text": "Could you tell me more about how you've been feeling lately?"
            })
            
        return followups

    def _check_suicide_risk(self, text):
        """Special check for suicide risk phrases that might be missed by regex"""
        high_risk_phrases = [
            "better off without me",
            "better off if i wasn't here", 
            "better off if i wasn't around",
            "no reason to live",
            "don't want to be here anymore",
            "want to end it all",
            "want to die"
        ]
        
        text_lower = text.lower()
        for phrase in high_risk_phrases:
            if phrase in text_lower:
                return True
        
        # Check specific suicidal terms - more restrictive than the general regex
        suicide_terms = ["suicide", "kill myself", "end my life", "take my own life", 
                         "death wish", "better off dead"]
        for term in suicide_terms:
            if term in text_lower:
                return True
        
        # Only check the regex if we already have other indicators
        if "symptoms" in self.extract_entities(text_lower) and \
           any(s["type"] == "suicidal" for s in self.extract_entities(text_lower).get("symptoms", [])):
            return True
        
        return False