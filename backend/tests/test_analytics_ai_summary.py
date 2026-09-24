import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.domain.ai_summary_entities import AIAnalyticsSummary, SummarySource
from src.use_cases.ai.analytics_summary import AnalyticsPlainLanguageSummaryUseCase


class _FakeLLM:
    def __init__(self, response_text=None, error=None):
        self.response_text = response_text
        self.error = error
        self.calls = 0

    def create_structured_completion(self, **_options):
        self.calls += 1
        if self.error:
            raise self.error
        return self.response_text


class _FakeRepository:
    def __init__(self):
        self.saved = []
        self._latest = None

    def get_latest(self, user_id):
        return self._latest

    def save(self, summary):
        summary.created_at = summary.created_at or datetime.utcnow()
        self.saved.append(summary)
        self._latest = summary
        return summary

    def touch_expiry(self, user_id, input_hash, expires_at):
        if self._latest and self._latest.input_hash == input_hash:
            self._latest.expires_at = expires_at
            return True
        return False


PERSONAL_SUMMARY = {
    'risk_level': 'Medium risk',
    'total_checks': 10,
    'high_risk_count': 3,
    'high_risk_rate': 30.0,
    'recent_high_risk_count': 1,
    'most_common_type': 'Banking Access & Payment',
    'type_insights': [{'type': 'Banking Access & Payment', 'share': 60, 'trend_direction': 'increasing', 'recent_count': 4, 'previous_count': 1}],
    'trend': [{'label': '2026-08', 'count': 4}, {'label': '2026-09', 'count': 6}],
}

COMMUNITY_SUMMARY = {
    'total_checks': 500,
    'scam_rate': 22.0,
    'most_common_type': 'Prize, Raffle & Reward',
    'trend_insight': 'Prize scams increased by 40% this month.',
    'seasonal_insight': 'Holiday shopping scams often increase this time of year.',
    'top_types': [{'type': 'Prize, Raffle & Reward', 'share': 30, 'trend_direction': 'increasing'}],
}

VALID_JSON = json.dumps({
    'headline': 'Watch out for banking scams',
    'risk_tag': 'medium',
    'current_status': ['You checked 10 messages.', '3 looked risky.'],
    'your_journey': ['Banking scam checks have increased recently.'],
    'community_trends': ['Prize scams are rising platform-wide.', 'Holiday scams are common this time of year.'],
    'watch_list': ['Urgent banking requests.', 'Prize or raffle messages.'],
    'tip': 'Verify banking requests through official channels.',
})


class AnalyticsPlainLanguageSummaryUseCaseTests(unittest.TestCase):
    def test_valid_gemini_response_is_stored_and_returned(self):
        llm = _FakeLLM(response_text=VALID_JSON)
        repo = _FakeRepository()
        use_case = AnalyticsPlainLanguageSummaryUseCase(llm, repo)

        result = use_case.get_summary('user-1', PERSONAL_SUMMARY, COMMUNITY_SUMMARY)

        self.assertEqual(result['risk_tag'], 'medium')
        self.assertEqual(result['source'], SummarySource.GEMINI)
        self.assertEqual(llm.calls, 1)
        self.assertEqual(len(repo.saved), 1)
        self.assertTrue(result['current_status'])
        self.assertTrue(result['your_journey'])
        self.assertTrue(result['community_trends'])
        self.assertTrue(result['watch_list'])

    def test_malformed_json_falls_back_to_deterministic_summary(self):
        llm = _FakeLLM(response_text='not json')
        repo = _FakeRepository()
        use_case = AnalyticsPlainLanguageSummaryUseCase(llm, repo)

        result = use_case.get_summary('user-1', PERSONAL_SUMMARY, COMMUNITY_SUMMARY)

        self.assertEqual(result['source'], SummarySource.FALLBACK)
        self.assertIn(result['risk_tag'], ('low', 'medium', 'high'))
        self.assertTrue(result['current_status'])
        self.assertTrue(result['community_trends'])

    def test_schema_violation_falls_back(self):
        bad_schema = json.dumps({
            'headline': 'x', 'risk_tag': 'extreme',
            'current_status': ['a'], 'your_journey': ['b'],
            'community_trends': ['c'], 'watch_list': ['d'], 'tip': 't',
        })
        llm = _FakeLLM(response_text=bad_schema)
        repo = _FakeRepository()
        use_case = AnalyticsPlainLanguageSummaryUseCase(llm, repo)

        result = use_case.get_summary('user-1', PERSONAL_SUMMARY, COMMUNITY_SUMMARY)

        self.assertEqual(result['source'], SummarySource.FALLBACK)

    def test_missing_section_falls_back(self):
        missing_section = json.dumps({
            'headline': 'x', 'risk_tag': 'low',
            'current_status': ['a'], 'your_journey': ['b'],
            'community_trends': [], 'watch_list': ['d'], 'tip': 't',
        })
        llm = _FakeLLM(response_text=missing_section)
        repo = _FakeRepository()
        use_case = AnalyticsPlainLanguageSummaryUseCase(llm, repo)

        result = use_case.get_summary('user-1', PERSONAL_SUMMARY, COMMUNITY_SUMMARY)

        self.assertEqual(result['source'], SummarySource.FALLBACK)

    def test_gemini_error_falls_back_without_raising(self):
        llm = _FakeLLM(error=RuntimeError('quota exceeded'))
        repo = _FakeRepository()
        use_case = AnalyticsPlainLanguageSummaryUseCase(llm, repo)

        result = use_case.get_summary('user-1', PERSONAL_SUMMARY, COMMUNITY_SUMMARY)

        self.assertEqual(result['source'], SummarySource.FALLBACK)

    def test_within_cooldown_returns_cached_summary_without_calling_llm(self):
        llm = _FakeLLM(response_text=VALID_JSON)
        repo = _FakeRepository()
        repo._latest = AIAnalyticsSummary(
            user_id='user-1',
            input_hash='some-other-hash',
            headline='Cached headline',
            risk_tag='low',
            current_status=['cached'],
            your_journey=['cached'],
            community_trends=['cached'],
            watch_list=['cached'],
            tip='cached tip',
            source=SummarySource.GEMINI,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=2),
        )
        use_case = AnalyticsPlainLanguageSummaryUseCase(llm, repo)

        result = use_case.get_summary('user-1', PERSONAL_SUMMARY, COMMUNITY_SUMMARY)

        self.assertEqual(result['headline'], 'Cached headline')
        self.assertEqual(llm.calls, 0)

    def test_cooldown_expired_but_stats_unchanged_extends_ttl_without_calling_llm(self):
        from src.use_cases.ai.analytics_summary import build_compact_stats, _hash_stats

        llm = _FakeLLM(response_text=VALID_JSON)
        repo = _FakeRepository()
        stats_hash = _hash_stats(build_compact_stats(PERSONAL_SUMMARY, COMMUNITY_SUMMARY))
        repo._latest = AIAnalyticsSummary(
            user_id='user-1',
            input_hash=stats_hash,
            headline='Still valid',
            risk_tag='medium',
            current_status=['same as before'],
            your_journey=['same'],
            community_trends=['same'],
            watch_list=['same'],
            tip='same tip',
            source=SummarySource.GEMINI,
            created_at=datetime.utcnow() - timedelta(hours=48),
            expires_at=datetime.utcnow() + timedelta(days=1),
        )

        with patch.dict('os.environ', {'AI_SUMMARY_COOLDOWN_HOURS': '24'}):
            use_case = AnalyticsPlainLanguageSummaryUseCase(llm, repo)
            result = use_case.get_summary('user-1', PERSONAL_SUMMARY, COMMUNITY_SUMMARY)

        self.assertEqual(result['headline'], 'Still valid')
        self.assertEqual(llm.calls, 0)

    def test_cooldown_expired_and_stats_changed_calls_llm_again(self):
        llm = _FakeLLM(response_text=VALID_JSON)
        repo = _FakeRepository()
        repo._latest = AIAnalyticsSummary(
            user_id='user-1',
            input_hash='stale-hash-from-different-stats',
            headline='Old summary',
            risk_tag='low',
            current_status=['old'],
            your_journey=['old'],
            community_trends=['old'],
            watch_list=['old'],
            tip='old tip',
            source=SummarySource.GEMINI,
            created_at=datetime.utcnow() - timedelta(hours=48),
            expires_at=datetime.utcnow() + timedelta(days=1),
        )

        with patch.dict('os.environ', {'AI_SUMMARY_COOLDOWN_HOURS': '24'}):
            use_case = AnalyticsPlainLanguageSummaryUseCase(llm, repo)
            result = use_case.get_summary('user-1', PERSONAL_SUMMARY, COMMUNITY_SUMMARY)

        self.assertEqual(llm.calls, 1)
        self.assertEqual(result['headline'], 'Watch out for banking scams')

    def test_get_cached_summary_returns_none_when_nothing_stored(self):
        llm = _FakeLLM(response_text=VALID_JSON)
        repo = _FakeRepository()
        use_case = AnalyticsPlainLanguageSummaryUseCase(llm, repo)

        result = use_case.get_cached_summary('user-1')

        self.assertIsNone(result)
        self.assertEqual(llm.calls, 0)

    def test_get_cached_summary_returns_stored_summary_without_calling_llm(self):
        llm = _FakeLLM(response_text=VALID_JSON)
        repo = _FakeRepository()
        repo._latest = AIAnalyticsSummary(
            user_id='user-1',
            input_hash='hash',
            headline='Previously generated',
            risk_tag='low',
            current_status=['a'],
            your_journey=['b'],
            community_trends=['c'],
            watch_list=['d'],
            tip='tip',
            source=SummarySource.GEMINI,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=2),
        )
        use_case = AnalyticsPlainLanguageSummaryUseCase(llm, repo)

        result = use_case.get_cached_summary('user-1')

        self.assertEqual(result['headline'], 'Previously generated')
        self.assertEqual(llm.calls, 0)


if __name__ == '__main__':
    unittest.main()

