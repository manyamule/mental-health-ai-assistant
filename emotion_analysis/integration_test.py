import os
import sys
import cv2
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from emotion_analyzer import EmotionAnalyzer
from face_detector import FaceDetector
from voice_analyzer import VoiceAnalyzer
from multimodal_integration import MultimodalAnalyzer
from parallel_analyzer import ParallelAnalyzer
from document_analyzer import DocumentAnalyzer
from intent_classification.intent_classifier import IntentClassifier

def check_intent_models():
    """Verify that intent models exist and are accessible"""
    models_dir = "../intent_classification/intent_models"
    required_files = ["classifier.pkl", "vectorizer.pkl", "label_encoder.pkl"]
    
    if not os.path.exists(models_dir):
        print(f"Intent models directory not found: {models_dir}")
        return False
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(os.path.join(models_dir, file)):
            missing_files.append(file)
    
    if missing_files:
        print(f"Missing intent model files: {', '.join(missing_files)}")
        print(f"Please run: python ../intent_classification/test_intent_classifier.py")
        return False
    
    return True

def display_result(result):
    """Display multimodal analysis results"""
    if not result:
        return
        
    print("\n----- ANALYSIS RESULTS -----")
    
    # Text analysis results
    print("\nDETECTED INTENTS:")
    for intent, score in result['text_analysis'].get('intents', {}).items():
        try:
            score_value = float(score) if isinstance(score, str) else score
            print(f"  - {intent}: {score_value:.2f}")
        except (ValueError, TypeError):
            print(f"  - {intent}: {score}")
    
    # Face analysis results
    print("\nFACIAL EMOTION:")
    if 'emotion' in result['face_analysis']:
        emotion = result['face_analysis']['emotion']
        confidence = result['face_analysis']['confidence']
        try:
            confidence_value = float(confidence) if isinstance(confidence, str) else confidence
            print(f"  - {emotion}: {confidence_value:.2f}")
        except (ValueError, TypeError):
            print(f"  - {emotion}: {confidence}")
    else:
        print("  - No clear facial emotion detected")
    
    # Voice analysis results
    print("\nVOICE ANALYSIS:")
    if result['voice_analysis'] and 'emotion' in result['voice_analysis']:
        # Show transcribed text if available
        if 'transcribed_text' in result['voice_analysis'] and result['voice_analysis']['transcribed_text']:
            print(f"  Transcribed speech: \"{result['voice_analysis']['transcribed_text']}\"")
        
        # Show overall emotion
        emotion = result['voice_analysis']['emotion']
        confidence = result['voice_analysis']['confidence']
        try:
            confidence_value = float(confidence) if isinstance(confidence, str) else confidence
            print(f"  Overall voice emotion: {emotion} ({confidence_value:.2f})")
        except (ValueError, TypeError):
            print(f"  Overall voice emotion: {emotion} ({confidence})")
        
        # Show text sentiment if available
        if 'text_sentiment' in result['voice_analysis'] and 'emotion' in result['voice_analysis']['text_sentiment']:
            ts = result['voice_analysis']['text_sentiment']
            print(f"  Text sentiment: {ts['emotion']} ({ts['confidence']:.2f})")
        
        # Show acoustic emotion if available
        if 'acoustic_emotion' in result['voice_analysis'] and 'emotion' in result['voice_analysis']['acoustic_emotion']:
            ae = result['voice_analysis']['acoustic_emotion']
            print(f"  Acoustic emotion: {ae['emotion']} ({ae['confidence']:.2f})")
    else:
        print("  - No clear voice emotion detected")
    
    # Emotional state summary
    if 'emotional_state' in result and result['emotional_state']['dominant_emotion']:
        state = result['emotional_state']
        print("\nOVERALL EMOTIONAL STATE:")
        print(f"  Dominant emotion: {state['dominant_emotion']}")
        print(f"  Valence (negative-positive): {state['valence']:.2f}")
        print(f"  Arousal (calm-excited): {state['arousal']:.2f}")
    
    # Suggested follow-ups
    print("\nSUGGESTED FOLLOW-UPS:")
    for followup in result.get('suggested_followups', []):
        print(f"  [{followup['priority']}] {followup['text']}")
    
    # Display generated response
    if 'generated_response' in result:
        print("\nGENERATED RESPONSE:")
        print(f"  {result['generated_response']['response']}")
        
        # Show validation issues if any
        if 'validation' in result['generated_response'] and not result['generated_response']['validation']['appropriate']:
            print("\nCLINICAL VALIDATION ISSUES:")
            for issue in result['generated_response']['validation']['issues']:
                print(f"  - {issue}")
    
    # After your existing print statements for analysis results
    if 'generated_response' in result:
        print("\nAI RESPONSE:")
        print(result['generated_response']['response'])
    
    print("\n----------------------------")

def test_integrated_system():
    """Test the integrated system with continuous facial and voice analysis"""
    # Initialize components
    emotion_analyzer = EmotionAnalyzer("models/my_model.h5")
    voice_analyzer = VoiceAnalyzer()
    
    if not check_intent_models():
        print("Intent models are missing or incomplete. Proceeding with limited functionality.")
    
    intent_classifier = IntentClassifier(model_dir="../intent_classification/intent_models")
    print(f"Intent classifier initialized. Models directory: {intent_classifier.model_dir}")

    # Check if models are loaded
    if intent_classifier.classifier is None:
        print("WARNING: Intent classifier models not loaded successfully.")
        print("Please ensure you've run training: python ../intent_classification/test_intent_classifier.py")

    face_detector = FaceDetector()
    
    # Create multimodal analyzer
    multimodal_analyzer = MultimodalAnalyzer(emotion_analyzer, intent_classifier, voice_analyzer)
    
    # Create parallel analyzer
    parallel_analyzer = ParallelAnalyzer(emotion_analyzer, voice_analyzer, multimodal_analyzer)
    
    # Check if models exist
    if not os.path.exists("models/my_model.h5"):
        print("Emotion model file not found. Please copy your h5 file.")
        return
        
    # Start webcam
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Could not open webcam")
        return
        
    # Start parallel analysis
    parallel_analyzer.start_processing(callback=display_result)
    
    print("Starting integrated test with continuous analysis...")
    print("Speak naturally while looking at the camera.")
    print("Press 'q' to quit, 's' to manually show last analysis results.")
    
    try:
        while True:
            # Read frame
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
                
            # Detect faces
            face_images, face_locations = face_detector.process_frame(frame)
            
            # Use the first face if detected
            if face_images:
                face_image = face_images[0]
                face_location = face_locations[0]
                
                # Add rectangle around face
                x, y, w, h = face_location
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Add frame to parallel analyzer
                parallel_analyzer.add_frame(face_image)
            
            # Get processed frame with emotion overlay if available
            processed_frame = parallel_analyzer.get_latest_processed_frame()
            if processed_frame is not None:
                # Display status info
                cv2.putText(frame, "System: Active", (10, frame.shape[0] - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Show speaking status
                if parallel_analyzer.speaking:
                    cv2.putText(frame, "Recording Speech...", (frame.shape[1] - 200, frame.shape[0] - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Display the frame
            cv2.imshow('Integrated Analysis', frame)
            
            # Process keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Manually display last analysis
                display_result(parallel_analyzer.latest_results)
        
    except KeyboardInterrupt:
        print("Stopped by user")
    
    finally:
        # Stop parallel analysis
        parallel_analyzer.stop_processing()
        
        # Release resources
        cap.release()
        cv2.destroyAllWindows()
        print("Resources released")

def test_document_analysis():
    """Test document analysis functionality"""
    analyzer = DocumentAnalyzer()
    
    # Test with a sample document
    sample_file = "sample_medical_record.pdf"  # Replace with a real test file path
    
    if os.path.exists(sample_file):
        # Extract text
        extracted_text = analyzer.process_document(sample_file)
        print("Extracted Text Sample:")
        print(extracted_text[:500] + "...\n")
        
        # Extract structured information
        info = analyzer.extract_medical_info(extracted_text)
        print("Extracted Information:")
        print(f"Patient Info: {info['patient_info']}")
        print(f"Medical History: {info['medical_history']}")
        print(f"Medications: {info['medications']}")
        print(f"Diagnoses: {info['diagnoses']}")
        print(f"Symptoms: {info['symptoms']}")
    else:
        print(f"Test file {sample_file} not found")

if __name__ == "__main__":
    test_document_analysis()
    test_integrated_system()