import os
import sys
import time
import matplotlib
from document_analyzer import DocumentAnalyzer
from document_upload import DocumentUploadUI
from run_voice_assistant import VoiceAssistant

matplotlib.use('Agg')  # Set non-interactive backend before any matplotlib import


import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

class EnhancedVoiceAssistant(VoiceAssistant):
    def __init__(self):
        # Initialize document analyzer
        self.document_analyzer = DocumentAnalyzer()
        self.document_info = None
        
        # Initialize base voice assistant components after document upload
        super().__init__()
    
    def process_document(self, file_path):
        """Process a document and extract information"""
        if not file_path:
            print("No document provided. Starting without document context.")
            return None
        
        print(f"Processing document: {os.path.basename(file_path)}")
        
        # Extract text from document
        extracted_text = self.document_analyzer.process_document(file_path)
        
        # Extract structured information
        extracted_info = self.document_analyzer.extract_medical_info(extracted_text)
        
        print("Document processed successfully!")
        print(f"Extracted {len(extracted_info['medical_history'])} medical history items")
        print(f"Extracted {len(extracted_info['medications'])} medications")
        print(f"Identified {len(extracted_info['diagnoses'])} potential diagnoses")
        
        # Store the extracted information
        self.document_info = extracted_info
        
        return extracted_info
    
    def _build_clinical_prompt(self, user_input, emotion_context, clinical_flags):
        """Override to include document context in prompt to LLM"""
        # Get the base prompt from parent class
        prompt = super()._build_clinical_prompt(user_input, emotion_context, clinical_flags)
        
        # Add document context if available
        if self.document_info:
            doc_context = "\nDOCUMENT CONTEXT:\n"
            
            # Add patient info
            if self.document_info["patient_info"]:
                doc_context += "Patient information:\n"
                for key, value in self.document_info["patient_info"].items():
                    doc_context += f"- {key}: {value}\n"
            
            # Add medical history
            if self.document_info["medical_history"]:
                doc_context += "\nMedical history:\n"
                for item in self.document_info["medical_history"]:
                    doc_context += f"- {item}\n"
            
            # Add medications
            if self.document_info["medications"]:
                doc_context += "\nMedications:\n"
                for med in self.document_info["medications"]:
                    doc_context += f"- {med}\n"
            
            # Add diagnoses
            if self.document_info["diagnoses"]:
                doc_context += "\nPotential diagnoses:\n"
                for diagnosis in self.document_info["diagnoses"]:
                    doc_context += f"- {diagnosis}\n"
            
            # Add symptoms
            if self.document_info["symptoms"]:
                doc_context += "\nReported symptoms:\n"
                for symptom in self.document_info["symptoms"]:
                    doc_context += f"- {symptom}\n"
            
            # Insert document context before user input
            prompt_parts = prompt.split("User:", 1)
            if len(prompt_parts) == 2:
                prompt = prompt_parts[0] + doc_context + "\n\nUser:" + prompt_parts[1]
            else:
                prompt += doc_context
        
        return prompt

def main():
    """Main entry point for the application"""
    print("Starting enhanced voice assistant system...")
    
    # Initialize document upload UI and wait for result
    document_file = None
    
    def handle_document_selection(file_path):
        nonlocal document_file
        document_file = file_path
    
    # Show document upload UI
    DocumentUploadUI(callback=handle_document_selection)
    
    # Create the enhanced voice assistant
    assistant = EnhancedVoiceAssistant()
    
    # Process document if provided
    if document_file:
        assistant.process_document(document_file)
    
    try:
        # Start the voice assistant
        assistant.start()
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        assistant.stop()

if __name__ == "__main__":
    main()