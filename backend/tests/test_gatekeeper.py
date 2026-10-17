from src.use_cases.ai.gatekeeper import GatekeeperUseCase, parse_gatekeeper_response


class FakeLLM:
    def __init__(self, content=None, error=None):
        self.content, self.error, self.calls = content, error, 0

    def create_chat_completion(self, messages, **options):
        self.calls += 1
        if self.error:
            raise self.error
        return {'choices': [{'message': {'content': self.content}}]}


def test_local_rules_reject_without_ai_call():
    llm = FakeLLM('{}')
    result = GatekeeperUseCase(llm).evaluate('Y')
    assert result['route'] == 'rejected'
    assert llm.calls == 0


def test_limited_route_parsed():
    llm = FakeLLM('{"route":"limited","reason_code":"too_vague","headline":"Vague promo",'
                  '"explanation":"Short.","observed_signs":["money"],"caution_level":"caution"}')
    result = GatekeeperUseCase(llm).evaluate('Sign up now to get 5k')
    assert result['route'] == 'limited'
    assert result['caution_level'] == 'caution'
    assert 'scam_score' not in result


def test_rejected_forces_no_caution():
    parsed = parse_gatekeeper_response(
        '{"route":"rejected","reason_code":"manipulation","caution_level":"high_caution","observed_signs":["x"]}')
    assert parsed['caution_level'] == 'none'
    assert parsed['observed_signs'] == []


def test_analyze_route():
    llm = FakeLLM('```json\n{"route":"analyze"}\n```')
    assert GatekeeperUseCase(llm).evaluate('Your GCash account is locked, verify at bit.ly/x now')['route'] == 'analyze'


def test_fail_open_on_error_and_garbage():
    assert GatekeeperUseCase(FakeLLM(error=RuntimeError('down'))).evaluate('hello there friend')['route'] == 'analyze'
    assert GatekeeperUseCase(FakeLLM('not json')).evaluate('hello there friend')['route'] == 'analyze'
    assert parse_gatekeeper_response('{"route":"banana"}') is None


def test_debt_threat_caught_locally_without_ai_call():
    llm = FakeLLM('{"route":"rejected","reason_code":"unrelated"}')
    result = GatekeeperUseCase(llm).evaluate('Papunta na kami dyan kasama kagawad, di ka kasi nagbabayad ng utang')
    assert result['route'] == 'limited'
    assert result['reason_code'] == 'threat'
    assert result['caution_level'] == 'high_caution'
    assert 'guidance' in result['suggested_action']
    assert llm.calls == 0


def test_threat_caught_even_if_ai_is_down():
    result = GatekeeperUseCase(FakeLLM(error=RuntimeError('down'))).evaluate(
        'Magbayad ka na kundi ipapakalat namin ang mga picture mo')
    assert result['reason_code'] == 'threat'


def test_ai_threat_code_forces_limited_route():
    parsed = parse_gatekeeper_response('{"route":"rejected","reason_code":"threat","caution_level":"none"}')
    assert parsed['route'] == 'limited'
    assert parsed['caution_level'] == 'high_caution'
    assert parsed['headline'] and parsed['explanation']


def test_ordinary_messages_not_flagged_as_threats():
    for text in ['Kuya ano oras tayo magkikita bukas?', 'Meeting with the kagawad tomorrow at 3pm',
                 'Reminder: your loan payment is due on the 15th']:
        llm = FakeLLM('{"route":"analyze"}')
        assert GatekeeperUseCase(llm).evaluate(text)['route'] == 'analyze'
        assert llm.calls == 1
