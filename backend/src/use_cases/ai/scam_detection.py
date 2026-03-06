"""
Use case for scam detection using the multi-head BERT model.
"""
import torch
import torch.nn.functional as F
import re
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class ScamDetectionUseCase:
    """Use case for detecting scams in messages."""
    
    def __init__(self, tokenizer, model, scam_types: dict):
        """
        Initialize the scam detection use case.
        
        Args:
            tokenizer: BERT tokenizer
            model: MultiHeadBERT model
            scam_types: Dictionary mapping scam type IDs to names
        """
        self.tokenizer = tokenizer
        self.model = model
        self.scam_types = scam_types
        self.temperature = 1.2
        self.bias_penalty = 3.0
    
    def detect(self, message: str) -> Dict[str, Any]:
        """
        Analyze a message for scam indicators.
        
        Args:
            message: The message text to analyze
            
        Returns:
            Dictionary containing:
                - scam_score: Probability that message is a scam (0-100)
                - legit_score: Probability that message is legitimate (0-100)
                - is_scam: Boolean indicating if message is likely a scam
                - scam_type: The most likely type of scam (if is_scam)
                - type_confidence: Confidence in the scam type classification (0-100)
        """
        logger.info(f"Analyzing message: {message[:100]}...")
        
        # Tokenize input
        inputs = self.tokenizer(message, return_tensors="pt", truncation=True)
        
        with torch.no_grad():
            # Get model predictions
            scam_logits, type_logits = self.model(**inputs)
            
            # Apply bias penalty if no suspicious links found
            link_patterns = r'https?://|www\.|bit\.ly|t\.co|goo\.gl|tinyurl\.com'
            if not re.search(link_patterns, message, re.IGNORECASE):
                logger.debug(f"No suspicious link found. Applying logit penalty of -{self.bias_penalty}")
                scam_logits[:, 1] -= self.bias_penalty
            
            # Apply temperature calibration
            calibrated_scam_logits = scam_logits / self.temperature
            calibrated_type_logits = type_logits / self.temperature
            
            # Calculate probabilities

            # !!! Alter softmax calculation based on variable presence
            # !!! Use bias calculations (maybe enforce scraping)
            scam_probs = F.softmax(calibrated_scam_logits, dim=1).squeeze()
            type_probs = F.softmax(calibrated_type_logits, dim=1).squeeze()
        
        # Extract results
        scam_score = float(scam_probs[1]) * 100
        legit_score = float(scam_probs[0]) * 100
        is_scam = scam_score > legit_score
        
        # Get scam type if it's a scam
        top_type_idx = torch.argmax(type_probs).item()
        scam_type = self.scam_types.get(top_type_idx, "Unknown")
        type_confidence = float(type_probs[top_type_idx]) * 100
        
        result = {
            "scam_score": round(scam_score, 2),
            "legit_score": round(legit_score, 2),
            "is_scam": is_scam,
            "label": "Scam" if is_scam else "Not Scam",
            "scam_type": scam_type if is_scam else None,
            "type_confidence": round(type_confidence, 2) if is_scam else None,
        }
        
        logger.info(f"Detection result: {result['label']} (Scam: {result['scam_score']:.1f}%, Legit: {result['legit_score']:.1f}%)")
        
        return result
