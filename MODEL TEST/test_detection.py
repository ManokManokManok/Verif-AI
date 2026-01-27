"""
Simple terminal-based script to test the scam detection model.
Run this script to test BERT + Gemma integration with text input.
"""
import sys
import os

# Add parent directory to path to import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from src.infrastructure.ai.loaders import load_multihead_model, load_gemma_model
from src.use_cases.ai.scam_detection import ScamDetectionUseCase
from src.use_cases.ai.llm_analysis import LLMAnalysisUseCase


def print_separator():
    print("=" * 80)


def print_header():
    print_separator()
    print("VERFAI SCAM DETECTION MODEL TEST")
    print_separator()
    print()


def print_results(message, bert_result, llm_result):
    """Pretty print the detection results"""
    print_separator()
    print("ANALYZED MESSAGE:")
    print_separator()
    print(message)
    print()
    
    print_separator()
    print("BERT ANALYSIS:")
    print_separator()
    print(f"Label:           {bert_result['label']}")
    print(f"Scam Score:      {bert_result['scam_score']:.2f}%")
    print(f"Legit Score:     {bert_result['legit_score']:.2f}%")
    
    if bert_result['is_scam']:
        print(f"Scam Type:       {bert_result['scam_type']}")
        print(f"Type Confidence: {bert_result['type_confidence']:.2f}%")
    print()
    
    if llm_result:
        print_separator()
        print("GEMMA LLM ANALYSIS:")
        print_separator()
        print(f"Summary: {llm_result['summary']}")
        print()
        
        if llm_result.get('key_markers') and len(llm_result['key_markers']) > 0:
            print("Key Linguistic Markers:")
            for idx, marker in enumerate(llm_result['key_markers'], 1):
                print(f"  {idx}. {marker}")
        print()
    
    print_separator()


def main():
    print_header()
    
    # Load models
    print("Loading models... (this may take a moment)")
    try:
        tokenizer, bert_model, scam_types = load_multihead_model()
        print("[OK] BERT model loaded successfully")
        
        gemma_llm = load_gemma_model()
        print("[OK] Gemma LLM loaded successfully")
        print()
    except Exception as e:
        print(f"[ERROR] Error loading models: {str(e)}")
        return
    
    # Main loop
    while True:
        print_separator()
        print("Enter a message to analyze (or 'quit' to exit):")
        print_separator()
        
        # Get user input
        message = input("> ").strip()
        
        if message.lower() in ['quit', 'exit', 'q']:
            print("\nGoodbye!")
            break
        
        if not message:
            print("[WARNING] Please enter a message to analyze.\n")
            continue
        
        print()
        print("Analyzing...")
        print()
        
        try:
            # Step 1: BERT Analysis
            scam_detection = ScamDetectionUseCase(tokenizer, bert_model, scam_types)
            bert_result = scam_detection.detect(message)
            
            # Step 2: Gemma Analysis (only if scam detected)
            llm_result = None
            if bert_result['is_scam']:
                llm_analysis = LLMAnalysisUseCase(gemma_llm)
                llm_result = llm_analysis.analyze(message, bert_result)
            
            # Print results
            print_results(message, bert_result, llm_result)
            
        except Exception as e:
            print(f"[ERROR] Error during analysis: {str(e)}")
            print()


if __name__ == "__main__":
    main()
