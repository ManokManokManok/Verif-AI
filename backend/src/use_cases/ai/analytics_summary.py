"""
Analytics Plain-Language Summary Use Case

Turns the already-computed, aggregated analytics data (both the user's own
stats and the platform-wide community stats) into a full plain-language
"translation" of the analytics page for non-technical users (elderly /
non-tech-savvy) - not a one-line blurb.

Design constraints (see project plan):
- Only aggregated/anonymous stats are ever sent to the model - no message
  content, no ref_ids, no raw timestamps, no user identifiers.
- The model must return a small set of FIXED, bounded JSON sections - never
  a raw paragraph - so the frontend can render it safely and predictably.
- Calls are cooled down per-user and persisted, so repeated button presses
  never re-trigger the (free-tier) Gemini API more than once per window.
"""

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ...domain.ai_summary_entities import AIAnalyticsSummary, SummarySource
from ...infrastructure.prompt_sanitizer import PromptSanitizer

logger = logging.getLogger(__name__)

# Fixed response schema the model must conform to (Gemini structured output).
# Bounded array sizes keep free-tier token usage predictable, but each item is
# meant to be a full explanatory paragraph, not a terse fact statement.
RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "headline": {"type": "string", "description": "A short, warm headline for the whole summary."},
        "risk_tag": {"type": "string", "enum": ["low", "medium", "high"]},
        "current_status": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 3,
            "description": "1-3 conversational paragraphs explaining where the user stands right now and why - not a list of numbers.",
        },
        "your_journey": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 2,
            "description": "1-2 paragraphs explaining how their pattern has changed over time and what that means for them, including simple advice on how to notice and respond to their most common scam type.",
        },
        "community_trends": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 2,
            "description": "1-2 paragraphs explaining what is happening across all users right now, why it matters, what scammers might try, and any seasonal context.",
        },
        "watch_list": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 2,
            "maxItems": 5,
            "description": "Specific, concrete things to watch out for based on this person's own patterns and the community trends.",
        },
        "tip": {"type": "string"},
    },
    "required": ["headline", "risk_tag", "current_status", "your_journey", "community_trends", "watch_list", "tip"],
}

_RISK_LEVEL_TO_TAG = {
    'high risk': 'high',
    'medium risk': 'medium',
    'low risk': 'low',
}

_SECTION_FIELDS = ("current_status", "your_journey", "community_trends", "watch_list")


def _risk_tag_from_level(risk_level: Optional[str]) -> str:
    return _RISK_LEVEL_TO_TAG.get((risk_level or '').strip().lower(), 'low')


def _cooldown_hours() -> int:
    return int(os.getenv('AI_SUMMARY_COOLDOWN_HOURS', '24'))


def _compact_type_insights(type_insights: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    compact = []
    for item in (type_insights or [])[:limit]:
        compact.append({
            "type": item.get("type"),
            "share": item.get("share"),
            "trend_direction": item.get("trend_direction"),
            "recent_count": item.get("recent_count"),
            "previous_count": item.get("previous_count"),
        })
    return compact


def _compact_trend(trend: List[Dict[str, Any]], limit: int = 6) -> List[Dict[str, Any]]:
    return [{"label": point.get("label"), "count": point.get("count")} for point in (trend or [])[-limit:]]


def build_compact_stats(personal_summary: Dict[str, Any], community_summary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract only the small, non-PII fields needed to generate the full summary."""
    community_summary = community_summary or {}

    personal = {
        "risk_level": personal_summary.get('risk_level', 'No data yet'),
        "total_checks": personal_summary.get('total_checks', 0),
        "high_risk_count": personal_summary.get('high_risk_count', 0),
        "high_risk_rate": personal_summary.get('high_risk_rate', 0),
        "recent_high_risk_count": personal_summary.get('recent_high_risk_count', 0),
        "most_common_type": personal_summary.get('most_common_type'),
        "type_insights": _compact_type_insights(personal_summary.get('type_insights')),
        "trend": _compact_trend(personal_summary.get('trend')),
    }
    community = {
        "total_checks": community_summary.get('total_checks', 0),
        "scam_rate": community_summary.get('scam_rate', 0),
        "most_common_type": community_summary.get('most_common_type'),
        "trend_insight": community_summary.get('trend_insight'),
        "seasonal_insight": community_summary.get('seasonal_insight'),
        "top_types": _compact_type_insights(community_summary.get('top_types')),
    }
    return {"personal": personal, "community": community}


def _hash_stats(stats: Dict[str, Any]) -> str:
    payload = json.dumps(stats, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _deterministic_fallback(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Non-AI summary built from the same rules the numeric sections already use."""
    personal = stats.get('personal', {})
    community = stats.get('community', {})
    risk_tag = _risk_tag_from_level(personal.get('risk_level'))
    total_checks = personal.get('total_checks', 0)

    if total_checks == 0:
        return {
            "headline": "Let's get started",
            "risk_tag": "low",
            "current_status": ["You haven't checked any messages yet, so there's nothing risky on your record right now - that's a good place to start."],
            "your_journey": ["Once you check a few messages, we'll be able to show you how your safety pattern changes over time."],
            "community_trends": [community.get('trend_insight') or "Other users are actively checking messages for scams right now, so it's a good habit to build."],
            "watch_list": ["Unexpected urgent requests for money or codes.", "Offers that seem too good to be true."],
            "tip": "Paste a suspicious message into the checker any time you're unsure.",
        }

    most_common = personal.get('most_common_type') or "a few different scam types"
    current_status = [
        f"Right now your account is showing a {risk_tag} risk level. Out of the {total_checks} messages you've checked, "
        f"{personal.get('high_risk_count', 0)} came back as genuinely dangerous, and most of those were about {most_common}."
    ]

    top_insight = (personal.get('type_insights') or [None])[0]
    if top_insight and top_insight.get('trend_direction') == 'increasing':
        your_journey = [
            f"Lately you've been seeing more messages about {top_insight.get('type')} than before, which usually means "
            "scammers are actively targeting this angle right now - if a message pressures you to act fast or share "
            "private details, that's the moment to slow down and double-check it through an official source."
        ]
    elif top_insight and top_insight.get('trend_direction') == 'decreasing':
        your_journey = [f"The number of messages about {top_insight.get('type')} has been easing off recently, which is a good sign - just keep checking anything that feels off."]
    else:
        your_journey = ["Your pattern of checks has stayed fairly steady over time, which suggests you're keeping a consistent eye on things."]

    community_trends = []
    if community.get('trend_insight'):
        community_trends.append(f"{community['trend_insight']} That kind of jump usually means scammers have found an angle that's working, so it's worth being extra cautious about it.")
    if community.get('seasonal_insight'):
        community_trends.append(community['seasonal_insight'])
    if not community_trends:
        community_trends.append(f"Across everyone using the app, {community.get('most_common_type') or 'a mix of scam types'} is coming up the most right now, so it's worth keeping an eye out for it too.")

    watch_list = [f"Messages about {most_common} that push you to act quickly or share details right away."]
    if community.get('most_common_type') and community.get('most_common_type') != most_common:
        watch_list.append(f"{community['most_common_type']}, since that's common across all users at the moment.")
    watch_list.append("Requests for passwords, one-time codes, or upfront payments.")

    tip = "Keep checking messages before you click links or share information."
    if risk_tag == 'high':
        tip = f"Be extra careful with messages about {most_common} - verify through official contacts first."

    return {
        "headline": "Your safety at a glance",
        "risk_tag": risk_tag,
        "current_status": current_status,
        "your_journey": your_journey,
        "community_trends": community_trends,
        "watch_list": watch_list,
        "tip": tip,
    }


class AnalyticsPlainLanguageSummaryUseCase:
    """Generates (or reuses) a full plain-language AI translation of a user's analytics page."""

    def __init__(self, llm_provider, repository):
        """
        Args:
            llm_provider: Object exposing create_structured_completion() (GenAIProvider)
            repository: AIAnalyticsSummaryRepository instance
        """
        self.llm = llm_provider
        self.repository = repository
        self.sanitizer = PromptSanitizer(max_length=4000, log_threats=True)

    def get_summary(
        self,
        user_id: str,
        personal_summary: Dict[str, Any],
        community_summary: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        stats = build_compact_stats(personal_summary, community_summary)
        input_hash = _hash_stats(stats)

        existing = self.repository.get_latest(user_id)
        cooldown = timedelta(hours=_cooldown_hours())
        now = datetime.utcnow()

        if existing and existing.created_at and (now - existing.created_at) < cooldown:
            # Still within cooldown: never call Gemini again yet, regardless of data changes.
            return self._to_response(existing)

        if existing and existing.input_hash == input_hash:
            # Situation hasn't changed - just extend the TTL instead of re-asking Gemini.
            expires_at = now + timedelta(days=2)
            self.repository.touch_expiry(user_id, input_hash, expires_at)
            existing.expires_at = expires_at
            return self._to_response(existing)

        summary = self._generate(user_id, stats, input_hash)
        return self._to_response(summary)

    def get_cached_summary(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Return a previously generated summary without ever calling Gemini.

        Used on page load so a returning user immediately sees their last
        summary instead of being asked to press the button again.
        """
        existing = self.repository.get_latest(user_id)
        if not existing:
            return None
        return self._to_response(existing)

    def _generate(self, user_id: str, stats: Dict[str, Any], input_hash: str) -> AIAnalyticsSummary:
        now = datetime.utcnow()
        expires_at = now + timedelta(days=2)

        try:
            parsed = self._call_gemini(stats)
            summary = AIAnalyticsSummary(
                user_id=user_id,
                input_hash=input_hash,
                headline=parsed['headline'],
                risk_tag=parsed['risk_tag'],
                current_status=parsed['current_status'],
                your_journey=parsed['your_journey'],
                community_trends=parsed['community_trends'],
                watch_list=parsed['watch_list'],
                tip=parsed['tip'],
                source=SummarySource.GEMINI,
                created_at=now,
                expires_at=expires_at,
            )
        except Exception as exc:
            logger.warning("[AI SUMMARY] Gemini generation failed, using fallback: %s", type(exc).__name__)
            fallback = _deterministic_fallback(stats)
            summary = AIAnalyticsSummary(
                user_id=user_id,
                input_hash=input_hash,
                headline=fallback['headline'],
                risk_tag=fallback['risk_tag'],
                current_status=fallback['current_status'],
                your_journey=fallback['your_journey'],
                community_trends=fallback['community_trends'],
                watch_list=fallback['watch_list'],
                tip=fallback['tip'],
                source=SummarySource.FALLBACK,
                created_at=now,
                expires_at=expires_at,
            )

        return self.repository.save(summary)

    def _call_gemini(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        stats_json = json.dumps(stats)
        sanitized = self.sanitizer.sanitize(stats_json, context="analytics_ai_summary")
        safe_stats = sanitized.sanitized_text

        prompt = f"""Here is aggregated, anonymous data from a fraud-detection app: the "personal" object
is one user's own scam-check activity, and the "community" object is platform-wide activity
across all users. No message content or personal identifiers are included.

{safe_stats}

You're talking directly to an elderly, non-technical person about their own safety data. Don't
just restate the numbers back to them like a report - think about what the numbers actually mean
for their life, and explain it the way a caring, knowledgeable friend would over a cup of coffee.

Write full, flowing, conversational paragraphs (not clipped fact-by-fact sentences). Reason about
the data first, then explain it in your own words:

- current_status: Tell them plainly where they stand and why - weave the risk level, totals, and
  their most common scam type into a natural explanation, not a checklist.
- your_journey: Look at their trend over time and explain what story it tells (improving, getting
  riskier, or steady) - and since this is their pattern, briefly explain how to recognize their
  most common scam type and what to actually do when they spot it.
- community_trends: Explain what's rising across the whole community right now and think through
  WHY that matters and what scammers are likely trying to do with that trend - mention relevant
  seasonal context (e.g. holiday, tax season) only if it's actually relevant to the data given.
- watch_list: Specific, concrete red flags to watch for, grounded in their own top scam types and
  the community trends - not generic security advice.
- tip: One clear, practical action they can take right now.

Be warm and reassuring even when the news is serious. Do not invent facts that aren't supported by
the data. Avoid raw percentages where a plain-language description reads more naturally, but you
may reference approximate numbers/counts when it helps tell the story."""

        messages = [
            {"role": "system", "content": "You are a warm, knowledgeable friend explaining someone's fraud-safety data to them in plain, conversational language. You reason about what the data means before explaining it - you never just recite numbers back as a bulleted report. Never invent facts not present in the data."},
            {"role": "user", "content": prompt},
        ]

        raw_text = self.llm.create_structured_completion(
            messages=messages,
            response_schema=RESPONSE_SCHEMA,
            max_tokens=1400,
            temperature=0.6,
        )
        parsed = json.loads(raw_text)
        self._validate_schema(parsed)
        return parsed

    @staticmethod
    def _validate_schema(parsed: Dict[str, Any]) -> None:
        if not isinstance(parsed, dict):
            raise ValueError("Response is not a JSON object")
        if parsed.get('risk_tag') not in ('low', 'medium', 'high'):
            raise ValueError("Invalid risk_tag")
        if not isinstance(parsed.get('headline'), str) or not parsed['headline'].strip():
            raise ValueError("Missing headline")
        for field_name in _SECTION_FIELDS:
            section = parsed.get(field_name)
            if not isinstance(section, list) or not section or not all(isinstance(item, str) and item.strip() for item in section):
                raise ValueError(f"Invalid section: {field_name}")
        if not isinstance(parsed.get('tip'), str) or not parsed['tip'].strip():
            raise ValueError("Missing tip")

    @staticmethod
    def _to_response(summary: AIAnalyticsSummary) -> Dict[str, Any]:
        return {
            "headline": summary.headline,
            "risk_tag": summary.risk_tag,
            "current_status": list(summary.current_status),
            "your_journey": list(summary.your_journey),
            "community_trends": list(summary.community_trends),
            "watch_list": list(summary.watch_list),
            "tip": summary.tip,
            "source": summary.source,
            "generated_at": summary.created_at.isoformat() if summary.created_at else None,
        }
