"""
LLM-based scam analysis use case.
Uses Gemma to provide human-readable summary and key linguistic markers.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class LLMAnalysisUseCase:
    """
    Use Gemma LLM to analyze scam messages and extract:
    - Summary: Short explanation of why it might be a scam
    - Key linguistic markers: List of red flags/indicators found in the text
    """
    
    def __init__(self, llm_model):
        """
        Initialize with a loaded Gemma model.
        
        Args:
            llm_model: Loaded llama_cpp.Llama instance
        """
        self.llm = llm_model
    
    def analyze(self, message: str, bert_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a message using Gemma LLM.
        
        Args:
            message: The text message to analyze
            bert_result: Dictionary containing BERT analysis results
                {
                    'is_scam': bool,
                    'scam_score': float,
                    'legit_score': float,
                    'scam_type': str,
                    'type_confidence': float
                }
        
        Returns:
            Dictionary with:
                {
                    'summary': str,  # Short summary of why it's a scam
                    'key_markers': List[str]  # List of key linguistic markers
                }
        """
        try:
            # Only analyze if BERT detected it as a scam
            if not bert_result.get('is_scam', False):
                return {
                    'summary': 'This message appears to be legitimate with no scam indicators detected.',
                    'key_markers': []
                }
            
            # Get summary
            summary = self._get_summary(message, bert_result)
            
            # Get key linguistic markers
            key_markers = self._get_key_markers(message, bert_result)
            
            return {
                'summary': summary,
                'key_markers': key_markers
            }
            
        except Exception as e:
            logger.error(f"[LLM ANALYSIS] Error: {str(e)}", exc_info=True)
            return {
                'summary': 'Unable to generate analysis summary.',
                'key_markers': []
            }
    
    def _get_summary(self, message: str, bert_result: Dict[str, Any]) -> str:
        """Generate a short summary using Gemma."""
        prompt = f"""Analyze this potentially fraudulent message and provide a SHORT summary (max 2 sentences) explaining why it appears to be a scam.

Message: "{message}"

Classifier detected: {bert_result['scam_type']} scam with {bert_result['scam_score']:.1f}% confidence.

Provide ONLY the summary, no introductions or extra text."""

        messages = [
            {
                "role": "system",
                "content": "You are a cybersecurity expert analyzing scam messages. Provide concise, clear summaries."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=150,
                temperature=0.3,
                stop=["<|im_start|>", "<|end|>", "\n\n\n"]
            )
            
            summary = response["choices"][0]["message"]["content"].strip()
            
            # Clean up any unwanted tokens
            for token in ["<|im_start|>", "<|end|>", "<end>", "end|", "<|end"]:
                summary = summary.replace(token, "").strip()
            
            return summary if summary else "This message contains indicators of fraudulent activity."
            
        except Exception as e:
            logger.error(f"[LLM SUMMARY] Error: {str(e)}")
            return "This message appears to be a scam based on pattern analysis."
    
    def _get_key_markers(self, message: str, bert_result: Dict[str, Any]) -> List[str]:
        """Extract key linguistic markers using Gemma."""
        prompt = f"""Analyze this scam message and identify the KEY LINGUISTIC MARKERS that indicate it's fraudulent.

Message: "{message}"

Detected as: {bert_result['scam_type']} scam

List 3-5 specific red flags or linguistic markers found in this message. Format as a simple bulleted list.
Each marker should be one short phrase (3-7 words). Focus on:
- Urgency tactics
- Suspicious links or contact methods
- Impersonation attempts
- Threats or promises
- Grammar/spelling issues

Output ONLY the bulleted list, nothing else."""

        messages = [
            {
                "role": "system",
                "content": "You are a cybersecurity expert identifying scam indicators. Output only bulleted markers, no explanations."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            response = self.llm.create_chat_completion(
                messages=messages,
                max_tokens=200,
                temperature=0.3,
                stop=["<|im_start|>", "<|end|>"]
            )
            
            markers_text = response["choices"][0]["message"]["content"].strip()
            
            # Clean up tokens
            for token in ["<|im_start|>", "<|end|>", "<end>", "end|"]:
                markers_text = markers_text.replace(token, "").strip()
            
            # Parse the bulleted list
            markers = []
            for line in markers_text.split('\n'):
                line = line.strip()
                # Remove bullet points and clean up
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    marker = line.lstrip('-•* ').strip()
                    if marker:
                        markers.append(marker)
            
            # Fallback if parsing failed
            if not markers:
                markers = [
                    "Urgency or pressure tactics",
                    "Suspicious sender or domain",
                    "Request for sensitive information"
                ]
            
            return markers[:5]  # Max 5 markers
            
        except Exception as e:
            logger.error(f"[LLM MARKERS] Error: {str(e)}")
            return ["Suspicious message patterns detected"]
