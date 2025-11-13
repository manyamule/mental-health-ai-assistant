import time
import os
from voice_analyzer import VoiceAnalyzer

def test_voice_analyzer():
    """Test the voice tone analyzer with speech-to-text and sentiment analysis"""
    analyzer = VoiceAnalyzer()
    
    print("\nThis test will record 5 seconds of audio and analyze your voice.")
    print("Please speak clearly and continuously after recording starts.")
    print("We'll analyze both the acoustic properties and the content of your speech.")
    
    input("Press Enter to begin recording...")
    
    # Start recording
    analyzer.start_recording(duration=5)
    
    # Wait for recording to complete
    while analyzer.is_recording():
        time.sleep(0.1)
        
    print("\nAnalyzing voice...")
    result = analyzer.analyze_emotion()
    
    print("\n----- VOICE ANALYSIS RESULTS -----")
    
    # Display transcribed text
    if "transcribed_text" in result:
        text = result["transcribed_text"]
        if text:
            print(f"\nTranscribed text: \"{text}\"")
        else:
            print("\nNo speech recognized.")
    
    # Display combined emotion
    if "emotion" in result:
        print(f"\nOverall emotion: {result['emotion']}")
        print(f"Confidence: {result['confidence']:.2f}")
        
        print("\nEmotion breakdown (text vs. acoustic):")
        if "text_sentiment" in result and "emotion" in result["text_sentiment"]:
            ts = result["text_sentiment"]
            print(f"  - Text sentiment: {ts['emotion']} (confidence: {ts['confidence']:.2f})")
            print(f"    Positive: {ts['pos']:.2f}, Negative: {ts['neg']:.2f}, Neutral: {ts['neu']:.2f}")
        
        if "acoustic_emotion" in result and "emotion" in result["acoustic_emotion"]:
            ae = result["acoustic_emotion"]
            print(f"  - Acoustic emotion: {ae['emotion']} (confidence: {ae['confidence']:.2f})")
        
        # Show all emotions after combining
        if "all_emotions" in result:
            print("\nFinal emotion distribution (after weighted combination):")
            for emotion, prob in sorted(result["all_emotions"].items(), key=lambda x: x[1], reverse=True):
                print(f"  - {emotion}: {prob:.4f}")
    
    # Display key audio features
    if "features" in result:
        print("\nKey acoustic features:")
        for feature in ['energy', 'pitch_mean', 'speech_rate', 'zero_crossing_rate', 'tempo']:
            if feature in result["features"]:
                print(f"  - {feature}: {result['features'][feature]:.4f}")
    else:
        print(f"Analysis failed: {result.get('message', 'Unknown error')}")
    
    print("\nRecorded audio saved to:", result.get("audio_file", "Not available"))
    
    # Check if visualizations were created
    vis_dir = os.path.join("temp_audio", "visualizations")
    if os.path.exists(vis_dir):
        print(f"Audio visualizations saved to: {vis_dir}")
    
    return result

if __name__ == "__main__":
    test_voice_analyzer()