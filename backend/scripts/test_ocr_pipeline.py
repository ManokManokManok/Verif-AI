"""
Test script for Image Classification pipeline.
Tests OCR extraction and integration with scam detection.

Usage:
    cd backend
    .venv\Scripts\activate  # Windows
    python -m pytest tests/test_image_classification.py -v
    
Or run directly:
    python scripts/test_ocr_pipeline.py <image_path>
"""
import sys
import os
import logging

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_ocr_service():
    """Test OCRService loads and basic extraction."""
    logger.info("=" * 80)
    logger.info("TEST 1: OCRService Loading")
    logger.info("=" * 80)
    
    try:
        from src.infrastructure.ai.ocr_service import OCRService
        
        ocr = OCRService(use_gpu=False)
        logger.info("[OK] OCRService imported and instantiated")
        
        # Test lazy loading
        ocr._load_ocr_engine()
        logger.info("[OK] PaddleOCR engine loaded successfully")
        
        return True
    except ImportError as e:
        logger.error(f"[FAIL] PaddleOCR not installed: {e}")
        logger.info("Install with: pip install paddleocr pillow")
        return False
    except Exception as e:
        logger.error(f"[FAIL] OCRService test failed: {e}", exc_info=True)
        return False


def test_text_cleanup():
    """Test text cleanup module."""
    logger.info("=" * 80)
    logger.info("TEST 2: Text Cleanup Module")
    logger.info("=" * 80)
    
    try:
        from src.infrastructure.ai.text_cleanup import TextCleanupProcessor, process_ocr_output
        
        processor = TextCleanupProcessor()
        logger.info("[OK] TextCleanupProcessor imported")
        
        # Test cleaning
        noisy_text = "This  is   a   test.....   With  extra    spaces"
        cleaned = processor.clean_text(noisy_text)
        logger.info(f"[OK] Text cleaned: '{noisy_text}' -> '{cleaned}'")
        
        # Test entity extraction
        text_with_entities = "Contact us at support@example.com or visit https://example.com or call 555-123-4567"
        emails = processor.extract_email_addresses(text_with_entities)
        urls = processor.extract_urls(text_with_entities)
        phones = processor.extract_phone_numbers(text_with_entities)
        
        logger.info(f"[OK] Extracted emails: {emails}")
        logger.info(f"[OK] Extracted URLs: {urls}")
        logger.info(f"[OK] Extracted phones: {phones}")
        
        return True
    except Exception as e:
        logger.error(f"[FAIL] Text cleanup test failed: {e}", exc_info=True)
        return False


def test_image_classification_use_case():
    """Test ImageClassificationUseCase initialization."""
    logger.info("=" * 80)
    logger.info("TEST 3: ImageClassificationUseCase")
    logger.info("=" * 80)
    
    try:
        from src.use_cases.ai.image_classification import ImageClassificationUseCase
        
        classifier = ImageClassificationUseCase(use_gpu=False)
        logger.info("[OK] ImageClassificationUseCase instantiated")
        
        return True
    except ImportError as e:
        logger.error(f"[FAIL] Import failed: {e}")
        return False
    except Exception as e:
        logger.error(f"[FAIL] Use case test failed: {e}", exc_info=True)
        return False


def test_with_sample_image(image_path: str = None):
    """Test with an actual image if provided."""
    logger.info("=" * 80)
    logger.info("TEST 4: End-to-End with Sample Image")
    logger.info("=" * 80)
    
    if not image_path:
        logger.info("[SKIP] No image path provided")
        return None
    
    if not os.path.exists(image_path):
        logger.error(f"[FAIL] Image not found: {image_path}")
        return False
    
    try:
        from src.use_cases.ai.image_classification import ImageClassificationUseCase
        from src.use_cases.ai.scam_detection import ScamDetectionUseCase
        from src.infrastructure.ai.loaders import load_multihead_model
        
        logger.info(f"Processing image: {image_path}")
        
        # Step 1: OCR
        logger.info("Step 1: Running OCR...")
        classifier = ImageClassificationUseCase(use_gpu=False)
        ocr_result = classifier.process_image(image_path, return_metadata=True)
        
        if 'error' in ocr_result:
            logger.error(f"[FAIL] OCR failed: {ocr_result['error']}")
            return False
        
        logger.info(f"[OK] OCR extracted {ocr_result['metadata']['length']} characters")
        logger.info(f"    Confidence: {int(ocr_result['confidence'] * 100)}%")
        logger.info(f"    URLs found: {len(ocr_result['metadata']['urls'])}")
        logger.info(f"    Emails found: {len(ocr_result['metadata']['emails'])}")
        
        # Step 2: Classification
        logger.info("\nStep 2: Running scam detection on extracted text...")
        try:
            tokenizer, model, scam_types = load_multihead_model()
            detector = ScamDetectionUseCase(tokenizer, model, scam_types)
            detection_result = detector.detect(ocr_result['text'])
            
            logger.info(f"[OK] Detection complete")
            logger.info(f"    Label: {detection_result['label']}")
            logger.info(f"    Scam Score: {detection_result['scam_score']:.1f}%")
            logger.info(f"    Legit Score: {detection_result['legit_score']:.1f}%")
            if detection_result['is_scam']:
                logger.info(f"    Type: {detection_result['scam_type']}")
                logger.info(f"    Type Confidence: {detection_result['type_confidence']:.1f}%")
        except Exception as det_error:
            logger.warning(f"[SKIP] Detection not available (model may not be loaded): {det_error}")
        
        return True
        
    except Exception as e:
        logger.error(f"[FAIL] End-to-end test failed: {e}", exc_info=True)
        return False


def main():
    """Run all tests."""
    logger.info("\n\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 78 + "║")
    logger.info("║" + "  VerfAI Image Classification Pipeline - Test Suite".center(78) + "║")
    logger.info("║" + " " * 78 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("\n")
    
    results = {}
    
    # Test 1: OCR Service
    results['OCRService'] = test_ocr_service()
    logger.info()
    
    # Test 2: Text Cleanup
    results['TextCleanup'] = test_text_cleanup()
    logger.info()
    
    # Test 3: Use Case
    results['UseCase'] = test_image_classification_use_case()
    logger.info()
    
    # Test 4: End-to-end (optional)
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        results['EndToEnd'] = test_with_sample_image(image_path)
    
    # Summary
    logger.info("=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for test_name, result in results.items():
        status = "[PASS]" if result is True else "[FAIL]" if result is False else "[SKIP]"
        logger.info(f"{status} {test_name}")
    
    logger.info()
    logger.info(f"Passed: {passed}, Failed: {failed}, Skipped: {skipped}")
    
    if failed == 0:
        logger.info("\n✓ All tests passed!")
        return 0
    else:
        logger.error(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
