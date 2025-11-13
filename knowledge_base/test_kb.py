from clinical_kb import ClinicalKnowledgeBase

def test_knowledge_base():
    kb = ClinicalKnowledgeBase()
    
    # Test retrieving disorder criteria
    mdd_criteria = kb.get_disorder_criteria("mdd")
    print("MDD Name:", mdd_criteria.get("name"))
    print("MDD Symptoms:", mdd_criteria.get("criteria", {}).get("symptoms", []))
    print("\n")
    
    # Test retrieving assessment questions
    phq9_questions = kb.get_assessment_questions("phq9")
    print(f"Found {len(phq9_questions)} PHQ-9 questions")
    for i, q in enumerate(phq9_questions[:3]):  # Print first 3 questions
        print(f"Q{i+1}: {q['text']}")
    print("\n")
    
    # Test retrieving risk factors
    suicide_risk = kb.get_risk_indicators("suicide")
    print("High Risk Suicide Indicators:", suicide_risk.get("high_risk_indicators", []))
    print("Response Protocol:", suicide_risk.get("response_protocol", {}).get("high_risk", ""))

if __name__ == "__main__":
    test_knowledge_base()