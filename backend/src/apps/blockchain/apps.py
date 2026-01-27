"""
Blockchain App Configuration
"""

from django.apps import AppConfig


class BlockchainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.apps.blockchain'
    verbose_name = 'Blockchain Anchoring'