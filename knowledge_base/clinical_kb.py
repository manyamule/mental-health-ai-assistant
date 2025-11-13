import json
import os

class ClinicalKnowledgeBase:
    def __init__(self, data_dir="knowledge_data"):
        self.data_dir = data_dir
        self.dsm_criteria = {}
        self.assessment_instruments = {}
        self.intervention_protocols = {}
        self.risk_factors = {}
        
        # Create data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            
        # Load data if available
        self._load_knowledge()
    
    def _load_knowledge(self):
        """Load knowledge data from files if they exist"""
        try:
            if os.path.exists(f"{self.data_dir}/dsm_criteria.json"):
                with open(f"{self.data_dir}/dsm_criteria.json", "r") as f:
                    self.dsm_criteria = json.load(f)
                    
            if os.path.exists(f"{self.data_dir}/assessment_instruments.json"):
                with open(f"{self.data_dir}/assessment_instruments.json", "r") as f:
                    self.assessment_instruments = json.load(f)
                    
            if os.path.exists(f"{self.data_dir}/intervention_protocols.json"):
                with open(f"{self.data_dir}/intervention_protocols.json", "r") as f:
                    self.intervention_protocols = json.load(f)
                    
            if os.path.exists(f"{self.data_dir}/risk_factors.json"):
                with open(f"{self.data_dir}/risk_factors.json", "r") as f:
                    self.risk_factors = json.load(f)
        except Exception as e:
            print(f"Error loading knowledge base data: {str(e)}")
    
    def get_disorder_criteria(self, disorder_id):
        """Get diagnostic criteria for a specific disorder"""
        return self.dsm_criteria.get(disorder_id, {})
    
    def get_assessment_questions(self, assessment_id, stage=None):
        """Get questions from a specific assessment instrument"""
        assessment = self.assessment_instruments.get(assessment_id, {})
        if stage and "stages" in assessment:
            return assessment.get("stages", {}).get(stage, [])
        return assessment.get("questions", [])
    
    def get_risk_indicators(self, risk_type=None):
        """Get risk indicators, optionally filtered by type"""
        if risk_type:
            return self.risk_factors.get(risk_type, [])
        return self.risk_factors
    
    def save_knowledge(self):
        """Save all knowledge data to files"""
        try:
            with open(f"{self.data_dir}/dsm_criteria.json", "w") as f:
                json.dump(self.dsm_criteria, f, indent=2)
                
            with open(f"{self.data_dir}/assessment_instruments.json", "w") as f:
                json.dump(self.assessment_instruments, f, indent=2)
                
            with open(f"{self.data_dir}/intervention_protocols.json", "w") as f:
                json.dump(self.intervention_protocols, f, indent=2)
                
            with open(f"{self.data_dir}/risk_factors.json", "w") as f:
                json.dump(self.risk_factors, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving knowledge base data: {str(e)}")
            return False