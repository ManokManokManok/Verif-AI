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

logger = logging.getLogger(__name__)

# Fixed response schema the model must conform to (Gemini structured output).
# Bounded array sizes keep free-tier token usage predictable. Each item is
# deliberately a substantial explanation rather than a terse fact statement.
RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "headline": {"type": "string", "description": "One warm, specific sentence that interprets the user's risk and most important pattern. Do not make it a generic label or repeat a raw metric."},
        "risk_tag": {"type": "string", "enum": ["low", "medium", "high"]},
        "current_status": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 3,
            "description": "1-3 substantial conversational paragraphs. Explain what the risk level means in everyday terms, connect the user's risky count and rate to the community rate when available, interpret their most common type, and reassure them that checking messages is protective. Do not write a list of disconnected facts.",
        },
        "your_journey": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 2,
            "description": "1-2 substantial conversational paragraphs. Read the trend points as a story over time, describe whether checking activity or risk is rising, falling, or steady, and use the type insight counts to explain what changed. Include a recognizable example of how their most common scam type may appear and exactly what they should do instead of responding.",
        },
        "community_trends": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 1,
            "maxItems": 2,
            "description": "1-2 substantial conversational paragraphs. Interpret the platform-wide trend and top types, explain why the change matters and what scammers are likely trying to get people to do, and use seasonal context only when the supplied insight supports it. Connect the community pattern back to this user without pretending the community data is their personal history.",
        },
        "watch_list": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 2,
            "maxItems": 5,
            "description": "3-5 specific, concrete red flags written as complete, vivid examples of messages or requests. Ground them in the user's patterns and community trends; avoid generic advice such as 'be careful'.",
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
_SUMMARY_VERSION = "analytics-summary-v3"

_TYPE_GLOSSARY = {
    "Banking Access & Payment": {
        "plain_meaning": "A message that pretends to involve a bank, payment service, or money transfer.",
        "typical_message": "It often says a payment failed or an account needs urgent verification.",
        "red_flags": ["Urgent requests for card details or one-time codes", "A payment link from an unexpected sender"],
        "what_to_do": "Open the official banking app yourself or call the number printed on your card.",
    },
    "Delivery & Customs": {
        "plain_meaning": "A message pretending that a parcel is delayed, held, or waiting for a fee.",
        "typical_message": "It says a delivery needs a small payment or personal details before it can arrive.",
        "red_flags": ["A parcel notice for something you did not order", "A fee request through a message link"],
        "what_to_do": "Check deliveries through the retailer or courier's official app or website.",
    },
    "Prize, Raffle & Reward": {
        "plain_meaning": "A message claiming you won money, a prize, or a special reward you did not expect.",
        "typical_message": "It asks you to pay a fee or share details to claim your supposed prize.",
        "red_flags": ["A surprise win for a contest you did not enter", "A fee required before a prize can be released"],
        "what_to_do": "Do not pay or share details; treat an unexpected prize as suspicious.",
    },
    "Tax, Banking, and Loan": {
        "plain_meaning": "A message using taxes, bank problems, or loan offers to pressure you into paying or sharing information.",
        "typical_message": "It threatens a penalty or promises quick money if you act immediately.",
        "red_flags": ["A tax or loan deadline that demands instant payment", "Requests for fees or bank details to unlock a loan"],
        "what_to_do": "Check your account or tax matter through the official website or a trusted contact.",
    },
    "Mobile and Digital": {
        "plain_meaning": "A message trying to take over your phone, digital wallet, or online account.",
        "typical_message": "It claims your device or account is at risk and asks you to tap a link, install something, or share a code.",
        "red_flags": ["A sudden request for a phone verification code", "A link asking you to fix or secure an account"],
        "what_to_do": "Open the real app yourself and never share a one-time code or allow unexpected remote access.",
    },
    "Tech and Online Account": {
        "plain_meaning": "A message pretending to be technical support or an online service protecting your account.",
        "typical_message": "It says your password or device is compromised and offers a link or remote help.",
        "red_flags": ["Unexpected remote-support requests", "A demand for a password or security code"],
        "what_to_do": "Contact the provider through its official app or website, not through the message.",
    },
    "Shopping and E-Commerce": {
        "plain_meaning": "A fake shopping offer, store, checkout, or delivery update designed to take money or card details.",
        "typical_message": "It advertises an unusually cheap deal or sends you to a suspicious checkout page.",
        "red_flags": ["Prices that are far below normal", "Payment links from unfamiliar shops"],
        "what_to_do": "Type the retailer's official address yourself and pay only through its trusted checkout.",
    },
    "Impersonation and Authority": {
        "plain_meaning": "A message pretending to come from a trusted person, company, government office, or authority.",
        "typical_message": "It uses an official-sounding identity and urgency to make the request feel legitimate.",
        "red_flags": ["Threats of immediate consequences", "A request to keep the conversation secret"],
        "what_to_do": "Contact the real organization through a number or website you already trust.",
    },
    "Financial and Investment": {
        "plain_meaning": "An offer promising fast profits, an easy loan, or a special investment opportunity.",
        "typical_message": "It promises guaranteed returns and pressures you to send money quickly.",
        "red_flags": ["Guaranteed profits with no risk", "Pressure to transfer money today"],
        "what_to_do": "Research the provider independently and never transfer money because a message creates urgency.",
    },
    "Health and Wellness": {
        "plain_meaning": "A message using a health product, treatment, or cure to collect money or private details.",
        "typical_message": "It promises a miracle result and asks you to pay or provide information immediately.",
        "red_flags": ["Miracle cures or guaranteed results", "Urgent payment for an unrequested treatment"],
        "what_to_do": "Ask a trusted medical professional and contact the provider through an official channel.",
    },
    "International or Cross-Border": {
        "plain_meaning": "A message involving an overseas transfer, shipment, or customs problem that needs quick action.",
        "typical_message": "It says money or a package is stuck abroad and asks for payment or personal details.",
        "red_flags": ["Unexpected overseas transaction or parcel", "Urgent customs or release fee"],
        "what_to_do": "Verify the shipment or transfer through the official company before paying anything.",
    },
    "Job, Business, and Work-from-Home": {
        "plain_meaning": "A fake job or business opportunity that asks for money or sensitive details before work begins.",
        "typical_message": "It promises easy income and asks for a registration fee or banking information.",
        "red_flags": ["Paying to receive a job", "Unverified employer requesting bank details"],
        "what_to_do": "Verify the employer independently and never pay to get hired.",
    },
    "Legal and Document": {
        "plain_meaning": "A message using a fake legal notice, fine, or document deadline to cause panic.",
        "typical_message": "It threatens a case or penalty unless you pay or respond immediately.",
        "red_flags": ["Threats of arrest or immediate legal action", "Payment demanded through an unusual channel"],
        "what_to_do": "Contact the court, agency, or business through an official contact you find yourself.",
    },
    "Property & Rental": {
        "plain_meaning": "A fake property listing or rental offer designed to collect a deposit before verification.",
        "typical_message": "It advertises an unusually good property and demands a quick deposit.",
        "red_flags": ["Deposit requested before viewing the property", "Landlord unavailable for independent verification"],
        "what_to_do": "Inspect and verify the property and landlord before sending any money.",
    },
    "Psychological, Urgency, & Emotional": {
        "plain_meaning": "A message using fear, guilt, panic, or emotional pressure to stop you from thinking clearly.",
        "typical_message": "It creates an emergency and insists you act before speaking to anyone else.",
        "red_flags": ["A demand to act immediately", "Requests to keep the situation secret"],
        "what_to_do": "Pause and speak with a trusted person before responding or sending anything.",
    },
    "Romance, Dating, and Relationship": {
        "plain_meaning": "A person builds an online relationship and later invents an emergency requiring money or gifts.",
        "typical_message": "It says someone you trust needs urgent financial help but cannot meet in person.",
        "red_flags": ["Repeated emergencies requiring money", "Pressure to keep the relationship or request secret"],
        "what_to_do": "Do not send money and discuss the request with someone you trust offline.",
    },
    "Account Verification & Phishing": {
        "plain_meaning": "A message pretending an account is locked or needs confirmation in order to steal login details.",
        "typical_message": "It asks you to verify an account through a link before a deadline.",
        "red_flags": ["An account-closure threat", "A login page reached through an unexpected link"],
        "what_to_do": "Open the official service yourself and check the account without using the message link.",
    },
}


def _rate_comparison(personal_rate: float, community_rate: float) -> str:
    if personal_rate <= 0 or community_rate <= 0:
        return "not enough comparable data"
    ratio = personal_rate / community_rate
    if ratio >= 1.75:
        return "much higher"
    if ratio >= 1.25:
        return "higher"
    if ratio <= 0.75:
        return "lower"
    return "about the same"


def _activity_trend(points: List[Dict[str, Any]]) -> str:
    counts = [point.get("count", 0) or 0 for point in points]
    if len(counts) < 2:
        return "not enough data to establish a direction"
    midpoint = max(1, len(counts) // 2)
    previous = sum(counts[:midpoint])
    recent = sum(counts[midpoint:])
    if recent > previous * 1.2:
        return "checking more often"
    if recent < previous * 0.8:
        return "checking less often"
    return "checking at a steady pace"


def _risk_tag_from_level(risk_level: Optional[str]) -> str:
    return _RISK_LEVEL_TO_TAG.get((risk_level or '').strip().lower(), 'low')


def _cooldown_hours() -> int:
    return int(os.getenv('AI_SUMMARY_COOLDOWN_HOURS', '720'))


def _compact_type_insights(type_insights: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
    compact = []
    for item in (type_insights or [])[:limit]:
        recent_count = item.get("recent_count", 0) or 0
        previous_count = item.get("previous_count", 0) or 0
        compact.append({
            "type": item.get("type"),
            "share": item.get("share"),
            "trend_direction": item.get("trend_direction"),
            "recent_count": recent_count,
            "previous_count": previous_count,
            "low_confidence": recent_count + previous_count < 5,
        })
    return compact


def _compact_trend(trend: List[Dict[str, Any]], limit: int = 6) -> List[Dict[str, Any]]:
    return [{"label": point.get("label"), "count": point.get("count")} for point in (trend or [])[-limit:]]


def build_compact_stats(personal_summary: Dict[str, Any], community_summary: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract only the small, non-PII fields needed to generate the full summary."""
    community_summary = community_summary or {}

    personal = {
        "summary_version": _SUMMARY_VERSION,
        "risk_level": personal_summary.get('risk_level', 'No data yet'),
        "total_checks": personal_summary.get('total_checks', 0),
        "total_scam_checks": personal_summary.get('total_scam_checks', 0),
        "high_risk_count": personal_summary.get('high_risk_count', 0),
        "high_risk_rate": personal_summary.get('high_risk_rate', 0),
        "recent_high_risk_count": personal_summary.get('recent_high_risk_count', 0),
        "most_common_type": personal_summary.get('most_common_type'),
        "type_insights": _compact_type_insights(personal_summary.get('type_insights')),
        "trend": _compact_trend(personal_summary.get('trend')),
    }
    personal_rate = personal.get('high_risk_rate', 0)
    if personal_summary.get('total_scam_checks') is not None and personal.get('total_checks'):
        personal_rate = round(personal.get('total_scam_checks', 0) / personal['total_checks'] * 100, 1)
    personal['scam_rate'] = personal_rate
    personal['activity_trend'] = _activity_trend(personal['trend'])
    if personal['trend']:
        personal['period_start'] = personal['trend'][0].get('label')
        personal['period_end'] = personal['trend'][-1].get('label')

    community = {
        "summary_version": _SUMMARY_VERSION,
        "total_checks": community_summary.get('total_checks', 0),
        "scam_rate": community_summary.get('scam_rate', 0),
        "high_risk_total": community_summary.get('high_risk_total', 0),
        "most_common_type": community_summary.get('most_common_type'),
        "trend_insight": community_summary.get('trend_insight'),
        "seasonal_insight": community_summary.get('seasonal_insight'),
        "top_types": _compact_type_insights(community_summary.get('top_types')),
    }
    personal['scam_rate_vs_community'] = _rate_comparison(personal['scam_rate'], community['scam_rate'])

    type_names = {
        item.get('type')
        for item in personal['type_insights'] + community['top_types']
        if item.get('type') in _TYPE_GLOSSARY
    }
    return {
        "summary_version": _SUMMARY_VERSION,
        "personal": personal,
        "community": community,
        "type_glossary": {name: _TYPE_GLOSSARY[name] for name in sorted(type_names)},
    }


def _hash_stats(stats: Dict[str, Any]) -> str:
    payload = json.dumps(stats, sort_keys=True, default=str)
    return f"{_SUMMARY_VERSION}:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"


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
    glossary = stats.get('type_glossary', {}).get(most_common, {})
    personal_rate = personal.get('scam_rate', personal.get('high_risk_rate', 0))
    community_rate = community.get('scam_rate', 0)
    comparison = personal.get('scam_rate_vs_community', 'not enough comparable data')
    current_status = [
        f"Your current safety status is {risk_tag} risk because {personal.get('high_risk_count', 0)} of your {total_checks} checks were in the high-risk range. "
        f"Your scam rate is {personal_rate}%, which is {comparison} than the community rate of {community_rate}%. "
        f"The most common pattern is {most_common}. Checking messages before acting is a useful protective habit, and this summary helps you see what to pause over."
    ]

    top_insight = (personal.get('type_insights') or [None])[0]
    if top_insight and top_insight.get('trend_direction') == 'increasing':
        type_name = top_insight.get('type')
        type_guide = stats.get('type_glossary', {}).get(type_name, {})
        your_journey = [f"From {personal.get('period_start') or 'the start of this period'} to {personal.get('period_end') or 'now'}, you have been {personal.get('activity_trend', 'checking messages')}. "
                        f"The {type_name} pattern rose from {top_insight.get('previous_count', 0)} checks to {top_insight.get('recent_count', 0)} recently, but this is an early signal when the sample is small. "
                        f"{type_guide.get('typical_message', 'These messages often create urgency and ask for information.')} {type_guide.get('what_to_do', 'Pause and verify through an official source instead of using the message.')}"]
    elif top_insight and top_insight.get('trend_direction') == 'decreasing':
        your_journey = [f"From {personal.get('period_start') or 'the start of this period'} to {personal.get('period_end') or 'now'}, you have been {personal.get('activity_trend', 'checking messages')}. "
                f"The {top_insight.get('type')} pattern is easing from {top_insight.get('previous_count', 0)} checks to {top_insight.get('recent_count', 0)} recently, which is encouraging. Keep checking anything that feels unusual before responding."]
    else:
        your_journey = [f"From {personal.get('period_start') or 'the start of this period'} to {personal.get('period_end') or 'now'}, you have been {personal.get('activity_trend', 'checking messages')}. "
                "That steady habit gives you a chance to pause and verify anything that feels unusual before responding."]

    community_trends = []
    if community.get('trend_insight'):
        community_trends.append(f"{community['trend_insight']} This is a community signal, not proof of what happened to you personally, and small category counts should be treated as early signals rather than firm trends.")
    if community.get('seasonal_insight'):
        community_trends.append(community['seasonal_insight'])
    if not community_trends:
        community_trends.append(f"Across everyone using the app, {community.get('most_common_type') or 'a mix of scam types'} is coming up the most right now, so it's worth keeping an eye out for it too.")

    watch_list = [glossary.get('typical_message', f"Messages about {most_common} that push you to act quickly or share details right away.")]
    watch_list.extend(glossary.get('red_flags', [])[:2])
    if community.get('most_common_type') and community.get('most_common_type') != most_common:
        watch_list.append(f"{community['most_common_type']}, since that's common across all users at the moment.")
    watch_list.append("Requests for passwords, one-time codes, or upfront payments.")

    tip = "Use the official app or a trusted phone number you already have to verify a request before clicking, paying, or sharing a code."
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

        is_current_format = existing and existing.input_hash.startswith(f"{_SUMMARY_VERSION}:")
        if existing and is_current_format and existing.created_at and (now - existing.created_at) < cooldown:
            # Still within cooldown: never call Gemini again yet, regardless of data changes.
            return self._to_response(existing)

        if existing and existing.input_hash == input_hash:
            # Situation hasn't changed - just extend the TTL instead of re-asking Gemini.
            expires_at = now + timedelta(days=31)
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
        expires_at = now + timedelta(days=31)

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

        prompt = f"""Here is aggregated, anonymous data from a fraud-detection app. The "personal" object
    is one user's own scam-check activity, and the "community" object is platform-wide activity
    across all users. No message content or personal identifiers are included. Treat the numbers as
    evidence to interpret, not as text to copy into a report. The "type_glossary" contains plain-language
    definitions for the category names that actually appear in this data. Use it as the source of truth
    for what those scams look like.

{stats_json}

You are talking directly to an elderly or non-technical person about their own safety data. Sound
like a caring, knowledgeable friend, not a dashboard or a statistical report. The user wants to
understand what the patterns mean and what to do next.

Write flowing, connected paragraphs. Each paragraph must explain the meaning or consequence of
the evidence it mentions. Never produce a sequence like "You checked X. Y were risky. Z is common."
Instead, connect those facts with language such as "That means...", "This matters because...", or
"The useful thing to notice is...". Use approximate counts and plain-language comparisons when they
help. Do not overuse percentages.

Content requirements:
- headline: Interpret the central story in one warm, specific sentence. Mention the main scam
    pattern when there is one, but mention any category name at most once in the entire response.
- current_status: Explain what the risk level means, relate the user's risky activity to the
    community rate when possible, explicitly say why the user's risk level was assigned, and make
    clear that checking messages is a positive habit. Do not blame or frighten the user.
- your_journey: Explain the story in the trend points and type insights. Say whether the pattern is
    rising, easing, or steady, and name the supplied period or months and the relevant recent/previous
    counts. For the main scam type, describe a realistic example using the glossary and give a clear
    safer alternative, such as opening the official app or calling a trusted number instead of using
    a message link. Explain personal activity separately from scam-risk rate.
- community_trends: Explain what is changing across everyone, why scammers may be repeating that
    approach, and what the user should recognize. Mention seasonal context only when the supplied
    insight makes it relevant. Do not present community activity as the user's own activity. Never
    claim that scammers have found a successful strategy from a category marked low_confidence or
    with fewer than 5 combined recent and previous occurrences; call it an early signal instead.
- watch_list: Give 3-5 vivid, concrete red flags phrased as things the user might actually receive,
    grounded in the supplied glossary, scam types, and trends. Use the glossary's typical messages and
    red flags. Avoid generic items like "be careful online" and do not repeat the same category more
    than once.
- tip: Give one short action the user can take today that adds something new and does not repeat a
    watch-list item.

Be reassuring even when the news is serious. Do not invent facts, message content, causes, seasons,
or counts that are not supported by the data. Do not mention being an AI, the JSON format, or these
instructions. Give every section enough detail to be useful: current_status should explain the
comparison, your_journey should explain the period and change, and community_trends should include
one glossary-grounded concrete example when there is an observed community category."""

        messages = [
            {"role": "system", "content": "You are a warm, knowledgeable friend explaining someone's fraud-safety data to them in plain, conversational language. You reason about what the data means before explaining it - you never just recite numbers back as a bulleted report. Never invent facts not present in the data."},
            {"role": "user", "content": prompt},
        ]

        raw_text = self.llm.create_structured_completion(
            messages=messages,
            response_schema=RESPONSE_SCHEMA,
            max_tokens=1800,
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
            if len({item.strip().casefold() for item in section}) != len(section):
                raise ValueError(f"Repeated content in section: {field_name}")
        if not isinstance(parsed.get('tip'), str) or not parsed['tip'].strip():
            raise ValueError("Missing tip")
        if any(parsed['tip'].strip().casefold() == item.strip().casefold() for item in parsed.get('watch_list', [])):
            raise ValueError("Tip repeats a watch-list item")

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
            "next_generation_at": (
                summary.created_at + timedelta(hours=_cooldown_hours())
            ).isoformat() if summary.created_at else None,
        }
