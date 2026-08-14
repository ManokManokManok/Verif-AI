"""
Performance monitoring script for VerfAi scam detection pipeline.
Session 1 Activity: Prototype Monitoring

Tests two critical functions independently with their own 3 test cases each:

  FUNCTION 1 — ScamDetectionUseCase.detect()
    Runs BERT multi-head classifier to determine scam vs legit + scam type.
    Test cases vary by message type (clear scam / borderline / legitimate).

  FUNCTION 2 — LLMAnalysisUseCase.analyze()
    Runs Gemma LLM to generate a summary and extract key linguistic markers.
    Test cases vary by scam complexity (short / long / multi-type indicators).

Run from within the backend virtual environment:
    cd backend
    .venv\\Scripts\\activate
    cd "../MODEL TEST"
    python test_performance.py
"""
import sys
import os
import time

# Add parent backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from src.infrastructure.ai.loaders import load_multihead_model, load_gemma_model
from src.use_cases.ai.scam_detection import ScamDetectionUseCase
from src.use_cases.ai.llm_analysis import LLMAnalysisUseCase
from src.use_cases.chatbot.general_chatbot import GeneralChatbotUseCase
from src.domain.chat_entities import ChatConversation


# ---------------------------------------------------------------------------
# Minimal in-memory mock for ConversationRepository
# Implements only the 3 methods GeneralChatbotUseCase.send_message() calls.
# No MongoDB connection required.
# ---------------------------------------------------------------------------
class _MockConversationRepo:
    def __init__(self):
        self._store = {}

    def create_conversation(self, user_id: str) -> ChatConversation:
        conv = ChatConversation.create_general(user_id=user_id, title="Perf Test")
        conv.id = f"mock-{len(self._store)}"
        self._store[conv.id] = conv
        return conv

    def get_by_id_for_user(self, conversation_id: str, user_id: str):
        return self._store.get(conversation_id)

    def save(self, conversation: ChatConversation) -> None:
        self._store[conversation.id] = conversation

SEP  = "=" * 80
SEP2 = "-" * 80

# ---------------------------------------------------------------------------
# FUNCTION 1 TEST CASES — ScamDetectionUseCase.detect()
# Varied inputs: clear scam with URL / urgency-only / legitimate
# ---------------------------------------------------------------------------
BERT_TEST_CASES = [
    (
        "Clear Scam (URL present)",
        "URGENT! Your BDO bank account has been suspended due to suspicious activity. "
        "Verify your identity immediately or lose access: http://bdo-secure-verify.xyz/login"
    ),
    (
        "Borderline (urgency, no URL)",
        "Congratulations! You have been selected as our lucky winner this month. "
        "Send your full name, address, and ID number to claim your PHP 50,000 prize today."
    ),
    (
        "Legitimate Message",
        "Hi! Just checking if you're free to meet this Saturday for the group project. "
        "Let me know what time works for you."
    ),
]

# ---------------------------------------------------------------------------
# FUNCTION 2 TEST CASES — LLMAnalysisUseCase.analyze()
# All confirmed scams so Gemma always runs; varied in length/complexity
# ---------------------------------------------------------------------------
LLM_TEST_CASES = [
    (
        "Short Scam (phishing link)",
        "Click here to verify your GCash account: http://gcash-verify.net/confirm",
        {   # pre-computed bert_result stub so Gemma always runs
            "is_scam": True,
            "scam_score": 94.5,
            "legit_score": 5.5,
            "scam_type": "Mobile / Digital Scam",
            "type_confidence": 88.2,
            "label": "Scam",
        }
    ),
    (
        "Long Scam (job offer fraud)",
        "Good day! We are hiring online encoders. Work from home, earn PHP 800–1,200/day. "
        "No experience needed. Just send your resume and a PHP 300 registration fee via GCash "
        "to 09171234567 to reserve your slot. Limited slots only! Apply now.",
        {
            "is_scam": True,
            "scam_score": 91.0,
            "legit_score": 9.0,
            "scam_type": "Job / Business / Work Scam",
            "type_confidence": 85.6,
            "label": "Scam",
        }
    ),
    (
        "Multi-indicator Scam (romance + money)",
        "Hello my love. I am a US soldier stationed overseas. I have a package of gold bars "
        "worth $500,000 that I want to ship to you for safekeeping. I just need you to pay "
        "the customs fee of $200 first. Please trust me, I love you.",
        {
            "is_scam": True,
            "scam_score": 97.1,
            "legit_score": 2.9,
            "scam_type": "Romance / Dating Scam",
            "type_confidence": 92.3,
            "label": "Scam",
        }
    ),
]


def fmt_time(seconds: float) -> str:
    return f"{seconds:.3f} sec"


# ---------------------------------------------------------------------------
# FUNCTION 1 — BERT detection timing
# ---------------------------------------------------------------------------

def bert_bottleneck(elapsed: float, is_scam: bool) -> str:
    if elapsed > 2.0:
        return "Slow BERT inference (large model)"
    if elapsed > 1.0:
        return "Moderate — tokenization + forward pass"
    if not is_scam:
        return "Fast — bias penalty short-circuited"
    return "Fast BERT inference"


def run_bert_tests(detection_uc):
    print(f"\n{SEP}")
    print("FUNCTION 1: ScamDetectionUseCase.detect()")
    print("Critical operation: BERT tokenization + multi-head forward pass")
    print(SEP)

    results = []
    for label, message in BERT_TEST_CASES:
        print(f"\n  [{label}]")
        print(f"  Message : {message[:75]}{'...' if len(message) > 75 else ''}")

        start = time.time()
        result = detection_uc.detect(message)
        end   = time.time()
        elapsed = end - start

        bottleneck = bert_bottleneck(elapsed, result["is_scam"])

        print(f"  Result  : {result['label']} | Scam: {result['scam_score']:.1f}% | "
              f"Legit: {result['legit_score']:.1f}%")
        if result["is_scam"]:
            print(f"  Type    : {result['scam_type']} ({result['type_confidence']:.1f}% conf.)")
        print(f"  Time    : {fmt_time(elapsed)}")
        print(f"  Bottleneck: {bottleneck}")

        results.append({
            "label":      label,
            "result":     result,
            "elapsed":    elapsed,
            "bottleneck": bottleneck,
        })

    # Performance table
    print(f"\n{SEP}")
    print("PERFORMANCE TABLE — Function 1: detect()")
    print(SEP)
    row = "{:<35}  {:<12}  {:<10}  {:<10}  {:<35}"
    print(row.format("Test Case", "Time", "Label", "Scam %", "Identified Bottleneck"))
    print(SEP2)
    for r in results:
        br = r["result"]
        print(row.format(
            r["label"][:35],
            fmt_time(r["elapsed"]),
            br["label"],
            f"{br['scam_score']:.1f}%",
            r["bottleneck"][:35],
        ))
    print(SEP)

    return results


# ---------------------------------------------------------------------------
# FUNCTION 2 — Gemma LLM analysis timing
# ---------------------------------------------------------------------------

def llm_bottleneck(elapsed: float, marker_count: int) -> str:
    if elapsed > 10.0:
        return "Very slow — LLM generation token limit"
    if elapsed > 5.0:
        return "Slow LLM generation (long output)"
    if marker_count > 4:
        return "Moderate — many markers extracted"
    return "Fast LLM completion (short output)"


def run_llm_tests(llm_uc):
    print(f"\n{SEP}")
    print("FUNCTION 2: LLMAnalysisUseCase.analyze()")
    print("Critical operation: Gemma chat completion (summary + key markers)")
    print(SEP)

    results = []
    for label, message, bert_stub in LLM_TEST_CASES:
        print(f"\n  [{label}]")
        print(f"  Message : {message[:75]}{'...' if len(message) > 75 else ''}")

        start = time.time()
        llm_result = llm_uc.analyze(message, bert_stub)
        end   = time.time()
        elapsed = end - start

        marker_count = len(llm_result.get("key_markers", []))
        bottleneck   = llm_bottleneck(elapsed, marker_count)

        print(f"  Summary : {llm_result['summary'][:100]}{'...' if len(llm_result['summary']) > 100 else ''}")
        print(f"  Markers : {marker_count} extracted")
        print(f"  Time    : {fmt_time(elapsed)}")
        print(f"  Bottleneck: {bottleneck}")

        results.append({
            "label":        label,
            "llm_result":   llm_result,
            "elapsed":      elapsed,
            "marker_count": marker_count,
            "bottleneck":   bottleneck,
        })

    # Performance table
    print(f"\n{SEP}")
    print("PERFORMANCE TABLE — Function 2: analyze()")
    print(SEP)
    row = "{:<35}  {:<12}  {:<10}  {:<35}"
    print(row.format("Test Case", "Time", "Markers", "Identified Bottleneck"))
    print(SEP2)
    for r in results:
        print(row.format(
            r["label"][:35],
            fmt_time(r["elapsed"]),
            str(r["marker_count"]),
            r["bottleneck"][:35],
        ))
    print(SEP)

    return results


# ---------------------------------------------------------------------------
# FUNCTION 3 TEST CASES — GeneralChatbotUseCase.send_message()
# Varied by question complexity: short tip / multi-step scenario / ambiguous
# ---------------------------------------------------------------------------
CHATBOT_TEST_CASES = [
    (
        "Simple Tip Request",
        "What are common signs of a phishing email?"
    ),
    (
        "Scenario-based Question",
        "I got a text saying I won a prize and need to pay a fee to claim it. "
        "The sender says it's from a government agency. What should I do?"
    ),
    (
        "Follow-up / Ambiguous Question",
        "I think I already clicked the link. Is it too late? What do I do now?"
    ),
]


def chatbot_bottleneck(elapsed: float, reply_len: int) -> str:
    if elapsed > 10.0:
        return "Very slow — long LLM generation (complex prompt)"
    if elapsed > 5.0:
        return "Slow — system prompt + history overhead"
    if reply_len > 400:
        return "Moderate — verbose reply increases token time"
    return "Fast LLM chat response"


def run_chatbot_tests(gemma_llm):
    print(f"\n{SEP}")
    print("FUNCTION 3: GeneralChatbotUseCase.send_message()")
    print("Critical operation: Gemma chat completion with system prompt + conversation history")
    print(SEP)

    mock_repo = _MockConversationRepo()
    chatbot_uc = GeneralChatbotUseCase(llm_model=gemma_llm, conversation_repository=mock_repo)

    results = []
    conv_id = None  # Reuse same conversation to test history overhead

    for label, question in CHATBOT_TEST_CASES:
        print(f"\n  [{label}]")
        print(f"  Question : {question[:75]}{'...' if len(question) > 75 else ''}")

        start = time.time()
        result = chatbot_uc.send_message(
            user_id="perf-test-user",
            message=question,
            conversation_id=conv_id,
        )
        end = time.time()
        elapsed = end - start

        conv_id = result["conversation_id"]   # chain messages in same conversation
        reply = result["response"]
        reply_len = len(reply)
        bottleneck = chatbot_bottleneck(elapsed, reply_len)

        print(f"  Reply    : {reply[:100]}{'...' if reply_len > 100 else ''}")
        print(f"  Msg count: {result['message_count']} in conversation")
        print(f"  Time     : {fmt_time(elapsed)}")
        print(f"  Bottleneck: {bottleneck}")

        results.append({
            "label":      label,
            "question":   question,
            "reply":      reply,
            "reply_len":  reply_len,
            "msg_count":  result["message_count"],
            "elapsed":    elapsed,
            "bottleneck": bottleneck,
        })

    # Performance table
    print(f"\n{SEP}")
    print("PERFORMANCE TABLE — Function 3: send_message()")
    print(SEP)
    row = "{:<35}  {:<12}  {:<10}  {:<10}  {:<35}"
    print(row.format("Test Case", "Time", "Reply Len", "Msg #", "Identified Bottleneck"))
    print(SEP2)
    for r in results:
        print(row.format(
            r["label"][:35],
            fmt_time(r["elapsed"]),
            str(r["reply_len"]) + " ch",
            str(r["msg_count"]),
            r["bottleneck"][:35],
        ))
    print(SEP)

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(SEP)
    print("VERFAI — SESSION 1 ACTIVITY: PROTOTYPE MONITORING")
    print("Two critical functions tested independently with 3 cases each")
    print(SEP)

    print("\nLoading models (one-time startup cost — not counted in function timing)...")
    t0 = time.time()
    try:
        tokenizer, bert_model, scam_types = load_multihead_model()
        t1 = time.time()
        print(f"  [OK] BERT model loaded     ({fmt_time(t1 - t0)})")

        gemma_llm = load_gemma_model()
        t2 = time.time()
        print(f"  [OK] Gemma LLM loaded      ({fmt_time(t2 - t1)})")
        print(f"  [OK] Total startup time    ({fmt_time(t2 - t0)})")
    except Exception as e:
        print(f"  [ERROR] {e}")
        return

    detection_uc = ScamDetectionUseCase(tokenizer, bert_model, scam_types)
    llm_uc       = LLMAnalysisUseCase(gemma_llm)

    # Run all three function test suites
    run_bert_tests(detection_uc)
    run_llm_tests(llm_uc)
    run_chatbot_tests(gemma_llm)

    print("\nDone. All three performance tables above can be submitted for the activity.")
    print(SEP)


if __name__ == "__main__":
    main()
