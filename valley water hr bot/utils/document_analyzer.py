# utils/document_analyzer.py
import os
import pytesseract
from PIL import Image
import PyPDF2
import json
import re
from datetime import datetime
from openai import OpenAI

class DocumentAnalyzer:
    """Class for analyzing documents uploaded by employees"""
    
    def __init__(self, openai_client=None):
        self.client = openai_client or OpenAI()
        self.document_types = {
            'pay_stub': ['gross pay', 'net pay', 'deductions', 'pay period'],
            'tax_form': ['w-2', '1099', 'tax', 'withholding'],
            'medical_bill': ['patient', 'amount due', 'insurance', 'provider'],
            'timecard': ['hours', 'overtime', 'time in', 'time out']
        }
    
    def identify_document_type(self, text):
        """Identify what type of document was uploaded"""
        text_lower = text.lower()
        scores = {}
        
        for doc_type, keywords in self.document_types.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[doc_type] = score
        
        return max(scores, key=scores.get) if max(scores.values()) > 0 else 'unknown'
    
    def extract_text_from_image(self, image_file):
        """Extract text from uploaded image using OCR"""
        try:
            image = Image.open(image_file)
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"Error extracting text from image: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_file):
        """Extract text from uploaded PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
            return ""
    
    def extract_key_information(self, text, doc_type):
        """Extract key fields based on document type"""
        extracted_data = {}
        
        if doc_type == 'pay_stub':
            # Extract pay stub information
            patterns = {
                'gross_pay': r'(?:gross pay|gross earnings)[\s:]*\$?([\d,]+\.?\d*)',
                'net_pay': r'(?:net pay|take home)[\s:]*\$?([\d,]+\.?\d*)',
                'pay_period': r'(?:pay period|period ending)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                'employee_id': r'(?:employee id|emp id)[\s:]*(\w+)',
            }
        elif doc_type == 'timecard':
            patterns = {
                'total_hours': r'(?:total hours)[\s:]*(\d+\.?\d*)',
                'regular_hours': r'(?:regular hours)[\s:]*(\d+\.?\d*)',
                'overtime_hours': r'(?:overtime|ot)[\s:]*(\d+\.?\d*)',
                'week_ending': r'(?:week ending)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            }
        elif doc_type == 'medical_bill':
            patterns = {
                'amount_due': r'(?:amount due|total due|balance)[\s:]*\$?([\d,]+\.?\d*)',
                'provider': r'(?:provider|doctor|physician)[\s:]*([A-Za-z\s]+)',
                'service_date': r'(?:service date|date of service)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
            }
        else:
            patterns = {}
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_data[field] = match.group(1)
        
        return extracted_data
    
    def analyze_document_with_ai(self, document_text, document_type, extracted_data, user_question):
        """Use AI to analyze document and answer questions"""
        prompt = f"""
        Analyze this {document_type} for the employee and answer their question.
        
        Document Text: {document_text[:1000]}...
        
        Extracted Information:
        {json.dumps(extracted_data, indent=2)}
        
        Employee Question: {user_question}
        
        Please provide:
        1. A direct answer to their question
        2. Any relevant calculations or explanations
        3. Important details they should know
        4. Suggestions for follow-up if needed
        
        Keep your response clear, friendly, and focused on helping the employee understand their document.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an HR assistant helping employees understand their documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error analyzing document: {e}")
            return "I'm sorry, I encountered an error analyzing your document. Please contact HR for assistance."