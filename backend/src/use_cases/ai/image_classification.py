"""
Use case for image classification pipeline: OCR → Text Cleanup → Ready for Detection
"""
import logging
from typing import Dict, Any, Union
from pathlib import Path

from src.infrastructure.ai.ocr_service import OCRService
from src.infrastructure.ai.text_cleanup import process_ocr_output

logger = logging.getLogger(__name__)


class ImageClassificationUseCase:
    """
    End-to-end image classification pipeline.
    
    Flow: Image → OCR Extract → Text Cleanup → Classification-Ready Text
    """
    
    def __init__(self, use_gpu: bool = False):
        """
        Initialize image classification use case.
        
        Args:
            use_gpu: Whether to use GPU for OCR (if available)
        """
        self.ocr_service = OCRService(use_gpu=use_gpu)
        logger.info("ImageClassificationUseCase initialized")
    
    def process_image(
        self, 
        image_input: Union[str, Path, bytes],
        return_metadata: bool = True
    ) -> Dict[str, Any]:
        """
        Process image through full pipeline.
        
        Args:
            image_input: File path (str/Path) or image bytes
            return_metadata: Include extracted metadata (emails, URLs, etc.)
            
        Returns:
            Dictionary with:
                - text: Classification-ready text
                - confidence: OCR confidence (0-1)
                - metadata: Extracted entities (emails, URLs, phones)
                - raw_text: Original OCR output (for debugging)
        """
        logger.info("Starting image classification pipeline")
        
        try:
            # Step 1: OCR Extraction
            logger.debug("Step 1: Running OCR extraction...")
            ocr_result = self.ocr_service.extract_text(image_input)
            
            if not ocr_result['text']:
                logger.warning("No text extracted from image")
                return {
                    'text': '',
                    'confidence': 0.0,
                    'metadata': {},
                    'raw_text': '',
                    'error': 'No text detected in image'
                }
            
            logger.debug(f"OCR extracted: {len(ocr_result['text'])} characters")
            
            # Step 2: Text Cleanup & Organization
            logger.debug("Step 2: Cleaning and organizing text...")
            processed = process_ocr_output(ocr_result)
            
            logger.info(
                f"Pipeline complete: {processed['metadata']['length']} chars, "
                f"confidence: {int(ocr_result['confidence']*100)}%"
            )
            
            # Step 3: Prepare final output
            result = {
                'text': processed['text'],
                'confidence': processed['confidence'],
                'raw_text': ocr_result['text'],  # For debugging
            }
            
            if return_metadata:
                result['metadata'] = processed['metadata']
            
            return result
            
        except Exception as e:
            logger.error(f"Image classification pipeline failed: {e}", exc_info=True)
            raise
    
    def process_batch(
        self, 
        image_paths: list,
        return_metadata: bool = True
    ) -> list:
        """
        Process multiple images.
        
        Args:
            image_paths: List of image file paths
            return_metadata: Include metadata for each
            
        Returns:
            List of results (one per image)
        """
        logger.info(f"Processing batch of {len(image_paths)} images")
        results = []
        
        for i, image_path in enumerate(image_paths, 1):
            try:
                logger.debug(f"Processing image {i}/{len(image_paths)}: {image_path}")
                result = self.process_image(image_path, return_metadata)
                results.append({
                    'image': str(image_path),
                    'result': result
                })
            except Exception as e:
                logger.error(f"Failed to process {image_path}: {e}")
                results.append({
                    'image': str(image_path),
                    'error': str(e)
                })
        
        logger.info(f"Batch processing complete. Success: {sum(1 for r in results if 'result' in r)}/{len(image_paths)}")
        return results
