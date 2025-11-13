from response_generator import ResponseGenerator
import json

def test_response_generator():
    """Test the response generator with different scenarios"""
    generator = ResponseGenerator()
    
    # Test scenarios including high risk ones
    test_scenarios = [
        {
            "name": "General greeting",
            "input": "Hello, how are you today?",
            "analysis": None
        },
        {
            "name": "Depression indicator",
            "input": "I've been feeling really down lately and nothing seems interesting anymore.",
            "analysis": {
                "text_analysis": {
                    "intents": {
                        "depression_indicator": 0.85,
                        "emotional_distress": 0.72
                    }
                },
                "face_analysis": {
                    "emotion": "sadness",
                    "confidence": 0.76
                },
                "emotional_state": {
                    "dominant_emotion": "sadness",
                    "valence": -0.7,
                    "arousal": -0.4
                }
            }
        },
        {
            "name": "Suicidal content",
            "input": "Sometimes I wonder if life is even worth living anymore.",
            "analysis": {
                "text_analysis": {
                    "intents": {
                        "suicidal_content": 0.68,
                        "depression_indicator": 0.85,
                        "emotional_distress": 0.91
                    }
                },
                "face_analysis": {
                    "emotion": "sadness",
                    "confidence": 0.82
                },
                "emotional_state": {
                    "dominant_emotion": "sadness",
                    "valence": -0.8,
                    "arousal": -0.5
                }
            }
        },
        {
            "name": "Emotional incongruence",
            "input": "Everything is great, I'm doing really well!",
            "analysis": {
                "text_analysis": {
                    "intents": {
                        "minimal_disclosure": 0.65,
                        "emotional_distress": 0.30
                    }
                },
                "face_analysis": {
                    "emotion": "sadness",
                    "confidence": 0.72
                },
                "voice_analysis": {
                    "emotion": "sadness",
                    "confidence": 0.65,
                    "text_sentiment": {
                        "emotion": "happiness",
                        "confidence": 0.88
                    }
                },
                "emotional_state": {
                    "dominant_emotion": "sadness",
                    "valence": -0.4,
                    "arousal": -0.2
                }
            }
        }
    ]
    
    # Run tests
    for scenario in test_scenarios:
        print(f"\n----- TESTING: {scenario['name']} -----")
        print(f"Input: \"{scenario['input']}\"")
        
        if scenario['analysis']:
            # Pretty print relevant analysis parts
            print("\nAnalysis:")
            if 'text_analysis' in scenario['analysis']:
                intents = scenario['analysis']['text_analysis'].get('intents', {})
                print(f"  Intents: {', '.join([f'{k}: {v:.2f}' for k, v in intents.items()])}")
            
            if 'face_analysis' in scenario['analysis']:
                face = scenario['analysis']['face_analysis']
                print(f"  Face: {face.get('emotion')} ({face.get('confidence', 0):.2f})")
                
            if 'emotional_state' in scenario['analysis']:
                state = scenario['analysis']['emotional_state']
                print(f"  State: {state.get('dominant_emotion')} (valence: {state.get('valence', 0):.2f})")
        
        # Generate response
        response_data = generator.generate_response(scenario['input'], scenario['analysis'])
        
        print("\nGenerated Response:")
        print(f"\"{response_data['response']}\"")
        
        if response_data.get('clinical_flags', {}).get('high_risk', False):
            print("\nClinical flags: HIGH RISK")
            print(f"Critical intents: {response_data.get('clinical_flags', {}).get('critical_intents', [])}")
        
        if response_data.get('validation', {}).get('issues', []):
            print("\nValidation issues:")
            for issue in response_data['validation']['issues']:
                print(f"  - {issue}")
        
        print("\n" + "-" * 50)

if __name__ == "__main__":
    test_response_generator()