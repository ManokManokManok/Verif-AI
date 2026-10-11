"""Tests that support messages are stored as ordinary user reports."""

import json
import os
from unittest.mock import Mock, patch

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')
django.setup()

from rest_framework.test import APIRequestFactory

from src.domain.admin_entities import ReportType
from src.interfaces.rest.reports_views import submit_report


class TestSupportReportSubmission:
    def setup_method(self):
        self.factory = APIRequestFactory()

    @patch('src.interfaces.rest.reports_views.SubmitUserReportUseCase')
    @patch('src.interfaces.rest.reports_views.get_admin_repository')
    @patch('src.interfaces.rest.reports_views.extract_user_from_request')
    def test_submits_support_as_standard_report(
        self,
        mock_extract,
        mock_get_repository,
        mock_use_case_class,
    ):
        mock_extract.return_value = {
            'user_id': 'user-123',
            'email': 'test@example.com',
            'roles': ['user'],
        }
        mock_get_repository.return_value = Mock()
        saved_report = Mock()
        saved_report.to_dict.return_value = {'report_type': 'support'}
        mock_use_case_class.return_value.execute.return_value = Mock(
            success=True,
            report=saved_report,
        )
        request = self.factory.post(
            '/api/reports/',
            data=json.dumps({
                'report_type': 'support',
                'title': 'Cannot update profile',
                'description': 'Category: Account and security\n\nI cannot change my username.',
            }),
            content_type='application/json',
            HTTP_AUTHORIZATION='Bearer test-token',
        )

        response = submit_report(request)

        assert response.status_code == 201
        assert json.loads(response.content)['data']['report_type'] == 'support'
        mock_use_case_class.return_value.execute.assert_called_once()
        assert mock_use_case_class.return_value.execute.call_args.kwargs['report_type'] == ReportType.SUPPORT
