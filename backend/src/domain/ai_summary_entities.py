"""
AI Analytics Summary Domain Entities

Domain entities for AI-generated, plain-language analytics summaries.
Only aggregated/anonymous statistics are ever used to produce these -
no message content or PII is stored or sent to the AI provider.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


class SummarySource:
    """Where a stored summary came from."""
    GEMINI = "gemini"
    FALLBACK = "fallback"


@dataclass
class AIAnalyticsSummary:
    """
    Domain entity representing a plain-language analytics summary
    generated for a single user.

    This is a full "translation" of the analytics page - not a one-line
    blurb - broken into fixed, rendering-safe sections the frontend
    consumes directly (never raw/unstructured AI text).
    """
    user_id: str
    input_hash: str  # hash of the compact stats object used to generate this summary
    headline: str
    risk_tag: str  # "low" | "medium" | "high"
    current_status: List[str] = field(default_factory=list)   # where they stand right now
    your_journey: List[str] = field(default_factory=list)     # how their pattern changed over time
    community_trends: List[str] = field(default_factory=list)  # what's rising platform-wide + what to watch for
    watch_list: List[str] = field(default_factory=list)        # short, specific things to be careful about
    tip: str = ""
    source: str = SummarySource.FALLBACK
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
