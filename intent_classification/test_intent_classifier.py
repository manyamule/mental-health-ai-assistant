from intent_classifier import IntentClassifier
import json

def test_classifier():
    # Load training data
    try:
        with open("training_data.json", "r") as f:
            training_data = json.load(f)
    except:
        from sample_training_data import create_sample_training_data
        training_data = create_sample_training_data()
    
    # Create and train classifier
    classifier = IntentClassifier()
    print("Training intent classifier...")
    classifier.train(training_data)
    print("Training complete")
    
    # Test some sample statements
    test_statements = [
        "I've been feeling really sad for the past week and I can't seem to enjoy anything",
        "I'm having trouble sleeping, I keep waking up at 3am every night",
        "The doctor gave me some new pills but they make me feel nauseous",
        "Sometimes I think everyone would be better off if I wasn't here",
        "I'm doing okay, nothing major has changed since last time"
    ]
    
    print("\nTesting classifier on sample statements:")
    for statement in test_statements:
        print("\nStatement:", statement)
        
        # Get intents
        intents = classifier.predict(statement)
        print("Detected Intents:")
        for intent, confidence in intents.items():
            print(f"  - {intent}: {confidence:.2f}")
        
        # Get entities
        entities = classifier.extract_entities(statement)
        print("Extracted Entities:")
        for entity_type, values in entities.items():
            print(f"  - {entity_type}: {values}")
        
        # Full analysis
        analysis = classifier.analyze_response(statement)
        print("Suggested Follow-up:")
        for followup in analysis["suggested_followups"]:
            print(f"  [{followup['priority']}] {followup['text']}")

if __name__ == "__main__":
    test_classifier()