# Model Test

Simple terminal-based script to test the BERT + Gemma scam detection model.

## Usage

1. Make sure you're in the backend virtual environment:
   ```bash
   cd backend
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

2. Run the test script:
   ```bash
   cd "../MODEL TEST"
   python test_detection.py
   ```

3. Enter messages to analyze when prompted
4. Type 'quit' or 'exit' to close the program

## What it tests

- ✅ BERT model loading
- ✅ Gemma LLM loading
- ✅ Scam detection classification
- ✅ Scam type identification
- ✅ LLM summary generation
- ✅ Key linguistic markers extraction

## Sample Test Messages

Try these sample messages:

**Scam Example:**
```
URGENT! Your bank account has been suspended. Click here immediately to verify: http://fake-bank.com/verify
```

**Legit Example:**
```
Hey, just wanted to confirm our meeting tomorrow at 3 PM. See you then!
```
