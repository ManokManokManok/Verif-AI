"""Analytics app configuration."""

from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.apps.analytics'
    label = 'analytics'
    verbose_name = 'Website Analytics'
