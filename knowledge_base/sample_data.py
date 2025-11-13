import os
import json
from clinical_kb import ClinicalKnowledgeBase

def create_sample_knowledge_data():
    kb = ClinicalKnowledgeBase()
    
    # DSM-5 criteria for Major Depressive Disorder
    kb.dsm_criteria["mdd"] = {
        "name": "Major Depressive Disorder",
        "code": "296.xx",
        "criteria": {
            "A": "Five (or more) of the following symptoms present during the same 2-week period; at least one of the symptoms is either (1) depressed mood or (2) loss of interest or pleasure.",
            "symptoms": [
                "Depressed mood most of the day, nearly every day",
                "Markedly diminished interest or pleasure in all, or almost all, activities",
                "Significant weight loss or weight gain, or decrease or increase in appetite",
                "Insomnia or hypersomnia nearly every day",
                "Psychomotor agitation or retardation nearly every day",
                "Fatigue or loss of energy nearly every day",
                "Feelings of worthlessness or excessive or inappropriate guilt",
                "Diminished ability to think or concentrate, or indecisiveness",
                "Recurrent thoughts of death, suicidal ideation, or suicide attempt"
            ],
            "B": "Symptoms cause clinically significant distress or impairment in functioning",
            "C": "Episode not attributable to physiological effects of a substance or medical condition",
            "D": "Occurrence not better explained by other psychotic disorders",
            "E": "No history of manic or hypomanic episode"
        },
        "severity": {
            "mild": "Few symptoms beyond minimum criteria, mild impairment",
            "moderate": "Symptoms or functional impairment between mild and severe",
            "severe": "Most symptoms present, marked interference with functioning"
        }
    }
    
    # PHQ-9 Depression Assessment
    kb.assessment_instruments["phq9"] = {
        "name": "Patient Health Questionnaire-9",
        "description": "Brief depression severity assessment instrument",
        "questions": [
            {
                "id": "phq1",
                "text": "Over the last 2 weeks, how often have you been bothered by little interest or pleasure in doing things?",
                "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                "scores": [0, 1, 2, 3]
            },
            {
                "id": "phq2",
                "text": "Over the last 2 weeks, how often have you been bothered by feeling down, depressed, or hopeless?",
                "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                "scores": [0, 1, 2, 3]
            },
            {
                "id": "phq3",
                "text": "Over the last 2 weeks, how often have you been bothered by trouble falling or staying asleep, or sleeping too much?",
                "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                "scores": [0, 1, 2, 3]
            },
            {
                "id": "phq4",
                "text": "Over the last 2 weeks, how often have you been bothered by feeling tired or having little energy?",
                "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                "scores": [0, 1, 2, 3]
            },
            {
                "id": "phq5",
                "text": "Over the last 2 weeks, how often have you been bothered by poor appetite or overeating?",
                "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                "scores": [0, 1, 2, 3]
            },
            {
                "id": "phq6",
                "text": "Over the last 2 weeks, how often have you been bothered by feeling bad about yourself — or that you are a failure or have let yourself or your family down?",
                "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                "scores": [0, 1, 2, 3]
            },
            {
                "id": "phq7",
                "text": "Over the last 2 weeks, how often have you been bothered by trouble concentrating on things, such as reading the newspaper or watching television?",
                "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                "scores": [0, 1, 2, 3]
            },
            {
                "id": "phq8",
                "text": "Over the last 2 weeks, how often have you been bothered by moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual?",
                "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                "scores": [0, 1, 2, 3]
            },
            {
                "id": "phq9",
                "text": "Over the last 2 weeks, how often have you been bothered by thoughts that you would be better off dead or of hurting yourself in some way?",
                "options": ["Not at all", "Several days", "More than half the days", "Nearly every day"],
                "scores": [0, 1, 2, 3]
            }
        ],
        "scoring": {
            "0-4": "Minimal or no depression",
            "5-9": "Mild depression",
            "10-14": "Moderate depression",
            "15-19": "Moderately severe depression",
            "20-27": "Severe depression"
        }
    }
    
    # Risk factors for suicide
    kb.risk_factors["suicide"] = {
        "high_risk_indicators": [
            "Current suicidal ideation with plan and intent",
            "Recent suicide attempt",
            "Severe hopelessness",
            "Psychosis",
            "Severe substance abuse"
        ],
        "moderate_risk_indicators": [
            "Suicidal ideation without specific plan or intent",
            "History of suicide attempts",
            "Moderate depression",
            "Recent major loss or negative life event"
        ],
        "protective_factors": [
            "Strong social support",
            "Effective coping skills",
            "Access to mental health care",
            "Sense of responsibility to family"
        ],
        "response_protocol": {
            "high_risk": "Immediate intervention required. Contact emergency services.",
            "moderate_risk": "Safety planning, frequent check-ins, consider referral to crisis services.",
            "low_risk": "Continue monitoring, ensure follow-up care and support resources."
        }
    }
    
    # Save the knowledge base
    kb.save_knowledge()
    print("Sample knowledge base data created successfully.")

if __name__ == "__main__":
    create_sample_knowledge_data()