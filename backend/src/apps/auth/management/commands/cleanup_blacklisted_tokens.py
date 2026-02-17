"""
Django management command to clean up expired blacklisted tokens from MongoDB.

Usage:
    python manage.py cleanup_blacklisted_tokens
    
This can be run:
- Manually when needed
- As a cron job (e.g., daily at 2 AM)
- Via a scheduler like Celery Beat (recommended for production)
"""

from django.core.management.base import BaseCommand
from src.infrastructure.mongodb.connection import get_mongo_client, get_database_name
from src.infrastructure.token_blacklist_service import MongoDBTokenBlacklistService


class Command(BaseCommand):
    help = 'Remove expired blacklisted tokens from MongoDB'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show how many tokens would be deleted without actually deleting them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        try:
            # Initialize the blacklist service
            client = get_mongo_client()
            db_name = get_database_name()
            blacklist_service = MongoDBTokenBlacklistService(client, db_name)
            
            if dry_run:
                # Count how many would be deleted
                from datetime import datetime
                collection = blacklist_service.blacklisted_tokens_collection
                count = collection.count_documents({
                    "expires_at": {"$lt": datetime.utcnow()}
                })
                self.stdout.write(
                    self.style.WARNING(f'[DRY RUN] Would delete {count} expired token(s)')
                )
            else:
                # Actually delete expired tokens
                deleted_count = blacklist_service.cleanup_expired_tokens()
                
                if deleted_count > 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'Successfully removed {deleted_count} expired token(s)')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('No expired tokens to clean up')
                    )
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error cleaning up tokens: {str(e)}')
            )
            raise
