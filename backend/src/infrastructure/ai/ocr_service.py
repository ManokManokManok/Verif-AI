"""
OCR Service using PaddleOCR for high-accuracy text extraction from images.
Optimized for scam detection model accuracy.
"""
import logging
from typing import Optional, List, Dict, Tuple
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class OCRService:
    """High-accuracy OCR service using PaddleOCR."""
    
    def __init__(self, use_gpu: bool = False, lang: List[str] = None):
        """
        Initialize OCR service.
        
        Args:
            use_gpu: Whether to use GPU acceleration (requires CUDA)
            lang: Languages to use (default: ['en'] for English)
        """
        self.use_gpu = use_gpu
        self.lang = lang or ['en']
        self._ocr = None
    
    def _load_ocr_engine(self):
        """Lazy load PaddleOCR to avoid startup delays."""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                logger.info(f"Initializing PaddleOCR with GPU={self.use_gpu}, langs={self.lang}")
                self._ocr = PaddleOCR(
                    use_angle_cls=True,  # For rotated text detection
                    use_gpu=self.use_gpu,
                    lang=self.lang,
                    show_log=False  # Reduce log noise
                )
                logger.info("PaddleOCR initialized successfully")
            except ImportError as e:
                raise ImportError(
                    "paddleocr not installed. Install with: pip install paddleocr"
                ) from e
        return self._ocr
    
    def extract_text(self, image_input) -> Dict[str, any]:
        """
        Extract text from image with high accuracy.
        
        Args:
            image_input: File path (str/Path) or image bytes
            
        Returns:
            Dictionary with:
                - text: Full extracted text
                - confidence: Average confidence score (0-1)
                - raw_results: List of detected text blocks
                - structured: Text with line breaks preserved
        """
        try:
            ocr = self._load_ocr_engine()
            
            # Convert bytes to path if needed
            if isinstance(image_input, bytes):
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                    f.write(image_input)
                    image_path = f.name
            else:
                image_path = str(image_input)
            
            logger.info(f"Running OCR on image: {image_path}")
            
            # Run OCR
            results = ocr.ocr(image_path, cls=True)
            
            if not results or not results[0]:
                logger.warning("No text detected in image")
                return {
                    'text': '',
                    'confidence': 0.0,
                    'raw_results': [],
                    'structured': ''
                }
            
            # Extract and organize text blocks
            text_blocks = []
            confidences = []
            
            for line in results[0]:
                text = line[1][0]
                conf = float(line[1][1])
                bbox = line[0]
                
                text_blocks.append({
                    'text': text,
                    'confidence': conf,
                    'bbox': bbox
                })
                confidences.append(conf)
            
            # Sort by vertical position (top to bottom) for reading order
            text_blocks_sorted = sorted(
                text_blocks,
                key=lambda b: min(p[1] for p in b['bbox'])  # Sort by top Y coordinate
            )
            
            # Combine text
            full_text = ' '.join([b['text'] for b in text_blocks_sorted])
            structured_text = '\n'.join([b['text'] for b in text_blocks_sorted])
            avg_confidence = np.mean(confidences) if confidences else 0.0
            
            logger.info(
                f"OCR extraction complete: {len(text_blocks)} blocks, "
                f"confidence: {avg_confidence:.2%}"
            )
            
            return {
                'text': full_text,
                'confidence': float(avg_confidence),
                'raw_results': text_blocks,
                'structured': structured_text
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}", exc_info=True)
            raise
    
    def extract_text_with_bbox(self, image_input) -> List[Dict]:
        """
        Extract text boxes with bounding box coordinates.
        Useful for analyzing spatial layout.
        
        Args:
            image_input: File path or image bytes
            
        Returns:
            List of dicts with: text, confidence, bbox (coordinates)
        """
        result = self.extract_text(image_input)
        return result['raw_results']
