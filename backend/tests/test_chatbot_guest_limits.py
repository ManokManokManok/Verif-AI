import os
import unittest
from unittest.mock import patch
from uuid import uuid4

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')
django.setup()

from rest_framework.test import APIRequestFactory
from django.core.files.uploadedfile import SimpleUploadedFile

from src.apps.chatbot import views
from src.apps.chatbot.guest_limits import claim_guest_use
from src.use_cases.chatbot.general_chatbot import STATIC_CHAT_PROMPTS


class GuestFeatureUsageTests(unittest.TestCase):
    def setUp(self):
        self.api_factory = APIRequestFactory()

    def test_each_feature_has_one_use_per_session(self):
        session_id = str(uuid4())

        self.assertTrue(claim_guest_use(session_id, 'text_chat'))
        self.assertFalse(claim_guest_use(session_id, 'text_chat'))
        self.assertTrue(claim_guest_use(session_id, 'image_analysis'))
        self.assertFalse(claim_guest_use(session_id, 'image_analysis'))

    def test_different_sessions_have_independent_allowances(self):
        self.assertTrue(claim_guest_use(str(uuid4()), 'text_chat'))
        self.assertTrue(claim_guest_use(str(uuid4()), 'text_chat'))

    @patch('src.apps.chatbot.views._handle_anonymous_chat')
    def test_chat_endpoint_rejects_second_guest_request(self, handle_anonymous_chat):
        session_id = str(uuid4())
        handle_anonymous_chat.return_value = {'response': 'ok', 'message_count': 2}

        first_request = self.api_factory.post(
            '/api/chat/message/',
            {'message': 'How do I identify a scam?'},
            format='json',
            HTTP_X_SESSION_ID=session_id,
        )
        first_response = views.send_message(first_request)

        second_request = self.api_factory.post(
            '/api/chat/message/',
            {'message': 'Another question'},
            format='json',
            HTTP_X_SESSION_ID=session_id,
        )
        second_response = views.send_message(second_request)

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(second_response.status_code, 429)
        self.assertEqual(second_response.data['error']['code'], 'GUEST_USE_LIMIT_REACHED')
        handle_anonymous_chat.assert_called_once()

    @patch('src.apps.chatbot.views.claim_guest_use', return_value=False)
    def test_static_chat_endpoint_uses_the_text_chat_allowance(self, claim_guest):
        request = self.api_factory.post(
            '/api/chat/static-message/',
            {'topic': next(iter(STATIC_CHAT_PROMPTS))},
            format='json',
            HTTP_X_SESSION_ID=str(uuid4()),
        )

        response = views.send_static_message(request)

        self.assertEqual(response.status_code, 429)
        claim_guest.assert_called_once()

    @patch('src.apps.chatbot.views.get_genai_provider')
    @patch('src.apps.chatbot.views.claim_guest_use', return_value=False)
    @patch('src.apps.chatbot.views._extract_user_id_from_jwt', return_value=(None, False))
    def test_image_analysis_rejects_guest_without_calling_gemini(
        self,
        _extract_user,
        claim_guest,
        get_genai_provider,
    ):
        request = self.api_factory.post(
            '/api/chat/image-analysis/',
            {'image': SimpleUploadedFile('sample.png', b'image-data', content_type='image/png')},
            format='multipart',
            HTTP_X_SESSION_ID=str(uuid4()),
        )

        response = views.analyze_image(request)

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.data['error']['code'], 'GUEST_USE_LIMIT_REACHED')
        claim_guest.assert_called_once()
        get_genai_provider.assert_not_called()


if __name__ == '__main__':
    unittest.main()
