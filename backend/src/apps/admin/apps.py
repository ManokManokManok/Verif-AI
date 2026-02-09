"""
Admin app configuration.
"""

from django.apps import AppConfig


class AdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.apps.admin'
    label = 'verfai_admin'  # Avoid conflict with django.contrib.admin
    verbose_name = 'Verif-AI Admin'
