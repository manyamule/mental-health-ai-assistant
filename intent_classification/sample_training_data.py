import json

def create_sample_training_data():
    training_data = [
        # Depression-related
        {
            "text": "I've been feeling really down lately, nothing seems to make me happy",
            "intents": ["symptom_report", "emotional_distress", "depression_indicator"]
        },
        {
            "text": "I don't enjoy things I used to like anymore",
            "intents": ["symptom_report", "anhedonia", "depression_indicator"]
        },
        {
            "text": "I'm so tired all the time even when I get enough sleep",
            "intents": ["symptom_report", "fatigue", "depression_indicator"]
        },
        {
            "text": "I feel worthless, like I'm just a burden to everyone",
            "intents": ["symptom_report", "negative_self_perception", "depression_indicator"]
        },
        
        # Anxiety-related
        {
            "text": "I worry constantly about everything",
            "intents": ["symptom_report", "worry", "anxiety_indicator"]
        },
        {
            "text": "Sometimes I get really panicky and feel like I can't breathe",
            "intents": ["symptom_report", "panic", "anxiety_indicator"]
        },
        {
            "text": "I'm always on edge waiting for something bad to happen",
            "intents": ["symptom_report", "hypervigilance", "anxiety_indicator"]
        },
        
        # Sleep issues
        {
            "text": "I have trouble falling asleep at night",
            "intents": ["symptom_report", "insomnia", "sleep_disturbance"]
        },
        {
            "text": "I wake up several times during the night",
            "intents": ["symptom_report", "insomnia", "sleep_disturbance"]
        },
        {
            "text": "I sleep too much, sometimes 12 hours and still feel tired",
            "intents": ["symptom_report", "hypersomnia", "sleep_disturbance"]
        },
        
        # Medication-related
        {
            "text": "The medication makes me feel dizzy sometimes",
            "intents": ["medication_mention", "side_effect_report"]
        },
        {
            "text": "I don't think the antidepressants are working for me",
            "intents": ["medication_mention", "treatment_concern"]
        },
        {
            "text": "I stopped taking my pills because they made me feel weird",
            "intents": ["medication_mention", "treatment_adherence_issue"]
        },
        
        # Suicidal content
        {
            "text": "Sometimes I think about ending it all",
            "intents": ["suicidal_content", "emotional_distress"]
        },
        {
            "text": "I don't know if I want to live anymore",
            "intents": ["suicidal_content", "emotional_distress"]
        },
        {
            "text": "Everyone would be better off without me",
            "intents": ["suicidal_content", "negative_self_perception"]
        },
        
        # General responses
        {
            "text": "I'm fine, nothing really to report",
            "intents": ["minimal_disclosure", "neutral_response"]
        },
        {
            "text": "I'm not sure what to say about that",
            "intents": ["uncertainty", "neutral_response"]
        },
        {
            "text": "Things have been pretty normal I guess",
            "intents": ["minimal_disclosure", "neutral_response"]
        },
        {
            "text": "I'd rather not talk about that right now",
            "intents": ["resistance", "boundary_setting"]
        }
    ]
    
    # Save as JSON
    with open("training_data.json", "w") as f:
        json.dump(training_data, f, indent=2)
    
    print(f"Created sample training data with {len(training_data)} examples")
    return training_data

if __name__ == "__main__":
    create_sample_training_data()