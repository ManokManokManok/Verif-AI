"""
Text cleanup and organization module for OCR output.
Optimizes extracted text for scam detection model accuracy.
"""
import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TextCleanupProcessor:
    """Clean and organize OCR text for classification."""
    
    # Patterns that often appear as OCR noise
    OCR_NOISE_PATTERNS = [
        r'\|+',  # Vertical lines misread as pipes
        r'[^\w\s\.\,\!\?\@\:\;\(\)\-\/]',  # Outlier symbols
    ]
    
    # Common OCR character replacements
    OCR_REPLACEMENTS = {
        'l': '1',  # lowercase L to 1
        'O': '0',  # O to zero
        'S': '5',  # S to 5
    }
    
    @staticmethod
    def clean_text(raw_text: str) -> str:
        """
        Clean OCR-extracted text by removing noise and fixing common errors.
        
        Args:
            raw_text: Raw OCR output
            
        Returns:
            Cleaned text
        """
        if not raw_text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', raw_text).strip()
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        # Normalize common OCR errors (careful - only for obviously wrong cases)
        # Only fix obvious patterns like "l00k" -> "look"
        text = re.sub(r'l00k', 'look', text, flags=re.IGNORECASE)
        text = re.sub(r'c1ick', 'click', text, flags=re.IGNORECASE)
        text = re.sub(r'v3rify', 'verify', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    @staticmethod
    def organize_text_for_classification(text: str, confidence: float) -> str:
        """
        Organize and structure text to maximize classifier input quality.
        
        Strategy:
        - Preserve natural line breaks for structure
        - Remove excessive punctuation
        - Normalize spacing
        - Keep URLs/links intact (important for scam detection)
        
        Args:
            text: Cleaned text
            confidence: OCR confidence score (0-1)
            
        Returns:
            Organized text ready for classification
        """
        if not text:
            return ""
        
        # If confidence is very low, add a disclaimer
        # (classifier should know input quality was compromised)
        confidence_score = int(confidence * 100)
        
        # Normalize line breaks (convert to single spaces initially)
        text = re.sub(r'\n\s*\n', ' | ', text)  # Preserve paragraph breaks as pipes
        text = re.sub(r'\n', ' ', text)  # Convert individual breaks to spaces
        
        # Remove excessive spaces
        text = re.sub(r'\s{2,}', ' ', text)
        
        # Preserve URLs (important for scam detection)
        # Extract URLs first
        urls = re.findall(r'https?://[^\s]+|www\.[^\s]+', text)
        
        # Clean text around URLs
        text = re.sub(r'https?://[^\s]+|www\.[^\s]+', 'URL_PLACEHOLDER', text)
        
        # Remove excessive punctuation chains (!!!!, ????, etc.)
        text = re.sub(r'([!?.]){3,}', r'\1\1', text)
        
        # Restore URLs with clear separation
        for url in urls:
            text = text.replace('URL_PLACEHOLDER', f' [ {url} ] ', 1)
        
        # Final cleanup
        text = re.sub(r'\s+', ' ', text).strip()
        
        logger.debug(
            f"Text organized for classification "
            f"(length: {len(text)}, confidence: {confidence_score}%)"
        )
        
        return text
    
    @staticmethod
    def extract_email_addresses(text: str) -> list:
        """Extract email addresses from text (useful context for classifier)."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
    
    @staticmethod
    def extract_urls(text: str) -> list:
        """Extract URLs from text (crucial for scam detection)."""
        url_pattern = r'https?://[^\s]+|www\.[^\s]+'
        return re.findall(url_pattern, text)
    
    @staticmethod
    def extract_phone_numbers(text: str) -> list:
        """Extract phone numbers from text."""
        # Basic pattern - adjust for your use case
        patterns = [
            r'\+?1?\s*[\(\-]?\d{3}[\)\-]?\s*\d{3}[\-]?\d{4}',  # US format
            r'\+\d{1,3}\s?\d{1,14}',  # International
        ]
        phone_numbers = []
        for pattern in patterns:
            phone_numbers.extend(re.findall(pattern, text))
        return list(set(phone_numbers))  # Remove duplicates


def process_ocr_output(ocr_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    End-to-end processing of OCR output for classification.
    
    Args:
        ocr_result: Output from OCRService.extract_text()
        
    Returns:
        Processed result optimized for classification
    """
    processor = TextCleanupProcessor()
    
    raw_text = ocr_result.get('text', '')
    confidence = ocr_result.get('confidence', 0.0)
    
    # Step 1: Clean
    cleaned_text = processor.clean_text(raw_text)
    
    # Step 2: Organize for classification
    organized_text = processor.organize_text_for_classification(cleaned_text, confidence)
    
    # Step 3: Extract entities (useful metadata)
    emails = processor.extract_email_addresses(organized_text)
    urls = processor.extract_urls(organized_text)
    phones = processor.extract_phone_numbers(organized_text)
    
    return {
        'text': organized_text,
        'confidence': confidence,
        'metadata': {
            'emails': emails,
            'urls': urls,
            'phone_numbers': phones,
            'length': len(organized_text),
            'has_urls': len(urls) > 0,
            'has_emails': len(emails) > 0,
        }
    }
