import os
import pytesseract
import cv2
import re
import uuid
from pdf2image import convert_from_path
from PIL import Image
import numpy as np

class DocumentAnalyzer:
    def __init__(self, upload_dir="document_uploads"):
        """Initialize document analyzer with upload directory"""
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)
        
        # Configure Tesseract path for Windows
        if os.name == 'nt':  # Windows
            pytesseract.pytesseract.tesseract_cmd = r'D:\\users\\Ajinkya\\programs\\Tesseract-OCR\\tesseract.exe'
    
    def save_document(self, file):
        """Save uploaded document and return the file path"""
        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        file_path = os.path.join(self.upload_dir, filename)
        file.save(file_path)
        return file_path
    
    def process_document(self, file_path):
        """Process document with OCR and return extracted text"""
        # Determine file type
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return self._process_pdf(file_path)
        elif ext in ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']:
            return self._process_image(file_path)
        else:
            return "Unsupported file format"
    
    def _process_pdf(self, pdf_path):
        """Process PDF document with fallback methods"""
        try:
            # Try using pdf2image/poppler first
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path)
            
            # Extract text from each page
            full_text = ""
            for i, image in enumerate(images):
                # Convert PIL image to OpenCV format
                open_cv_image = np.array(image) 
                open_cv_image = open_cv_image[:, :, ::-1].copy() 
                
                # Process image and extract text
                text = self._process_cv_image(open_cv_image)
                full_text += f"\n--- Page {i+1} ---\n{text}"
            
            return full_text
            
        except Exception as e:
            print(f"PDF conversion with poppler failed: {e}")
            print("Trying alternative PDF processing method...")
            
            try:
                # Alternative method using PyMuPDF (fitz)
                import fitz  # PyMuPDF
                
                full_text = ""
                doc = fitz.open(pdf_path)
                
                # First try to extract text directly
                for i, page in enumerate(doc):
                    text = page.get_text()
                    if text.strip():  # If we got meaningful text
                        full_text += f"\n--- Page {i+1} ---\n{text}"
                    else:
                        # If text extraction fails, render page to image and use OCR
                        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                            pix.height, pix.width, pix.n)
                        
                        # Convert to BGR for OpenCV if needed
                        if pix.n == 4:  # RGBA
                            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                        elif pix.n == 3:  # RGB
                            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                            
                        # Process image and extract text
                        text = self._process_cv_image(img)
                        full_text += f"\n--- Page {i+1} ---\n{text}"
                
                return full_text
                
            except Exception as e2:
                print(f"Alternative PDF processing failed: {e2}")
                return f"PDF processing failed. Please install Poppler or PyMuPDF: {e} / {e2}"
    
    def _process_image(self, image_path):
        """Process image document"""
        # Load image with OpenCV
        image = cv2.imread(image_path)
        return self._process_cv_image(image)
    
    def _process_cv_image(self, image):
        """Process CV2 image and extract text with OCR"""
        # Preprocess image for better OCR results
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Apply dilation to make text clearer
        kernel = np.ones((1, 1), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=1)
        
        # Run OCR
        text = pytesseract.image_to_string(dilated)
        return text
    
    def extract_medical_info(self, text):
        """Extract relevant medical information from OCR text with improved immunization detection"""
        # Dictionary to store extracted information
        info = {
            "patient_info": {},
            "medical_history": [],
            "medications": [],
            "allergies": [],
            "immunizations": [],
            "diagnoses": [],
            "raw_text": text if isinstance(text, str) else str(text)
        }
        
        # Ensure text is a string before processing
        if not isinstance(text, str):
            print(f"Warning: Expected string for text, got {type(text)}")
            if hasattr(text, '__str__'):
                text = str(text)
            else:
                print("Cannot convert text to string. Returning empty results.")
                return info
        
        # Print preview of extracted text
        print("\n--- First 500 characters of extracted text ---")
        print(text[:500] + "..." if len(text) > 500 else text)
        print()
        
        # Extract patient information
        patient_name_patterns = [
            r'(?:Patient|Name)[:\s]+([A-Za-z\s]+)',
            r'Patient Information\s*\n([A-Za-z\s]+)'
        ]
        
        for pattern in patient_name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info["patient_info"]["name"] = match.group(1).strip()
                break
        
        # Extract DOB/Birth Date
        dob_patterns = [
            r'(?:DOB|Date of Birth|Birth Date)[:\s]+([A-Za-z0-9,\s]+)',
            r'Birth Date\s*\n([A-Za-z0-9,\s]+)'
        ]
        
        for pattern in dob_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info["patient_info"]["dob"] = match.group(1).strip()
                break
        
        # Extract address
        address_pattern = r'\d+\s+[A-Za-z\s]+(?:Dr|Road|Street|Ave|Lane|Blvd|Boulevard)[\s,]+([A-Za-z\s]+),\s+([A-Za-z\s]+),\s+(\d+)'
        address_match = re.search(address_pattern, text)
        if address_match:
            info["patient_info"]["address"] = address_match.group(0).strip()
        
        # Extract immunization status - NEW!
        immunization_patterns = [
            (r'Chicken Pox \(Varicella\):\s*([A-Z\s]+)', "Chicken Pox (Varicella)"),
            (r'Measles:\s*([A-Z\s]+)', "Measles"),
            (r'Hepatitis [A-Z](?:\s+vaccination)?[:\s]+\s*([A-Za-z]+)', "Hepatitis")
        ]
        
        for pattern, name in immunization_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                status = match.group(1).strip()
                if status.lower() not in ['n/a', 'none', '']:
                    info["immunizations"].append(f"{name}: {status}")
                    
                    # For immune status, also add to medical history
                    if "immune" in status.lower():
                        if "not" in status.lower() or "non" in status.lower():
                            info["medical_history"].append(f"Not immune to {name}")
                        else:
                            info["medical_history"].append(f"Immune to {name}")
                    
                    # For vaccinations, add to medical history
                    if "yes" in status.lower() or "vaccinated" in status.lower():
                        info["medical_history"].append(f"{name} vaccination")
        
        # Extract allergies - improved to recognize "N/A"
        allergies_match = re.search(r'(?:List any allergies|Allergies)[:\s]+([^\n]+)', text, re.IGNORECASE)
        if allergies_match:
            allergies_text = allergies_match.group(1).strip()
            if allergies_text.lower() != "n/a" and allergies_text.lower() != "none":
                for allergy in re.split(r'[,;]', allergies_text):
                    clean_allergy = allergy.strip()
                    if clean_allergy and clean_allergy.lower() not in ["n/a", "none", "/"]:
                        info["allergies"].append(clean_allergy)
        
        # Extract medications - improved to recognize "N/A"
        med_match = re.search(r'(?:List any medication|Medications)[^:]*:[^\n]*([^\n]+)', text, re.IGNORECASE)
        if med_match:
            meds_text = med_match.group(1).strip()
            if meds_text.lower() != "n/a" and meds_text.lower() != "none":
                for med in re.split(r'[,;]', meds_text):
                    clean_med = med.strip()
                    if clean_med and clean_med.lower() not in ["n/a", "none", "/"]:
                        info["medications"].append(clean_med)
        
        # Medical problems/diagnoses - improved to recognize "N/A"
        problems_match = re.search(r'(?:Medical Problems|Diagnoses)[^:]*:([^\n]+)', text, re.IGNORECASE)
        if problems_match:
            problems_text = problems_match.group(1).strip()
            if problems_text.lower() != "n/a" and problems_text.lower() != "none":
                for problem in re.split(r'[,;]', problems_text):
                    clean_problem = problem.strip()
                    if clean_problem and clean_problem.lower() not in ["n/a", "none", "/"]:
                        info["diagnoses"].append(clean_problem)
        
        return info
    
    def extract_with_llm(self, text):
        """Use Gemini to extract medical information with improved instructions for N/A handling"""
        from google.generativeai import GenerativeModel
        import google.generativeai as genai
        
        # Load API key from environment
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            print("Warning: No Google API key found. Cannot use LLM for document extraction.")
            return None
        
        # Configure the Gemini model
        genai.configure(api_key=api_key)
        model = GenerativeModel("gemini-2.0-flash")
        
        # Create a prompt for information extraction
        prompt = f"""
        Extract medical information from this document. Return information in JSON format:
        
        {text[:4000]}  # Limiting to first 4000 chars to avoid token limits
        
        Extract these fields and follow these important guidelines:
        
        1. patient_info: Extract name, age, gender, DOB, address if found
        2. medical_history: List of past medical conditions AND immunization status (include immune/not immune status)
        3. immunizations: List specific immunization status like "Chicken Pox: IMMUNE"
        4. medications: List of medications mentioned (if marked "N/A", return empty list)
        5. allergies: List of allergies mentioned (if marked "N/A", return empty list)
        6. symptoms: List of symptoms mentioned
        7. diagnoses: List of diagnoses mentioned (if marked "N/A", return empty list)
        
        IMPORTANT: If a field is explicitly marked as "N/A" or "None" in the document, return an empty list for that field.
        For medications, allergies, and diagnoses, only include actual medical information, not the absence of it.
        
        Format as proper JSON. Only return the JSON with no additional text.
        """
        
        try:
            response = model.generate_content(prompt)
            response_text = response.text
            
            # Extract only the JSON part from the response
            import json
            import re
            
            # Try to find JSON in the response
            json_match = re.search(r'```json\s*({.*?})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # If no code block, try to extract the entire JSON object
                json_match = re.search(r'({[\s\S]*})', response_text)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = response_text
            
            # Clean up the string and parse JSON
            json_str = json_str.replace('```', '').strip()
            
            # Attempt to fix common JSON errors
            json_str = re.sub(r'(\w+):', r'"\1":', json_str)  # Add quotes to keys
            json_str = re.sub(r',\s*}', r'}', json_str)  # Remove trailing commas
            
            extracted_info = json.loads(json_str)
            
            # Normalize keys
            normalized_info = {
                "patient_info": extracted_info.get("patient_info", {}),
                "medical_history": extracted_info.get("medical_history", []),
                "medications": extracted_info.get("medications", []),
                "allergies": extracted_info.get("allergies", []),
                "immunizations": extracted_info.get("immunizations", []),
                "symptoms": extracted_info.get("symptoms", []),
                "diagnoses": extracted_info.get("diagnoses", []),
                "raw_text": text
            }
            
            return normalized_info
        except Exception as e:
            print(f"Error using LLM for extraction: {e}")
            return None