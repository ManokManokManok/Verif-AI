from django.core.management.base import BaseCommand
from src.infrastructure.mongodb.connection import get_mongo_client, get_database_name


class Command(BaseCommand):
    help = 'Seed default roles and permissions into MongoDB'

    def handle(self, *args, **options):
        client = get_mongo_client()
        db_name = get_database_name()
        db = client[db_name]
        roles_collection = db.roles

        # Define default roles with permissions
        default_roles = [
            {
                "name": "user",
                "permissions": [
                    "view_profile",
                    "update_profile",
                    "analyze_content",
                    "view_history",
                    "submit_report"  # Users can submit reports
                ],
                "description": "Standard user with basic permissions"
            },
            {
                "name": "admin",
                "permissions": [
                    # Basic user permissions
                    "view_profile",
                    "update_profile",
                    "analyze_content",
                    "view_history",
                    "submit_report",
                    # User management permissions
                    "manage_users",
                    "delete_users",
                    "view_all_users",
                    "manage_roles",
                    "reset_user_password",
                    # Admin dashboard permissions
                    "view_model_health",
                    "view_analysis_stats",
                    "view_user_stats",
                    "manage_user_reports",
                    "view_system_logs",
                    # System permissions
                    "view_analytics",
                    "manage_system"
                ],
                "description": "Administrator with full system access"
            },
            {
                "name": "moderator",
                "permissions": [
                    # Basic user permissions
                    "view_profile",
                    "update_profile",
                    "analyze_content",
                    "view_history",
                    "submit_report",
                    # Limited admin permissions
                    "view_all_users",
                    "view_analytics",
                    "view_analysis_stats",
                    "view_user_stats",
                    "manage_user_reports"  # Can handle user reports
                ],
                "description": "Moderator with elevated permissions for content review"
            }
        ]

        # Check and insert roles
        inserted_count = 0
        updated_count = 0
        
        for role_data in default_roles:
            existing_role = roles_collection.find_one({"name": role_data["name"]})
            
            if existing_role:
                # Update existing role
                roles_collection.update_one(
                    {"name": role_data["name"]},
                    {"$set": {
                        "permissions": role_data["permissions"],
                        "description": role_data["description"]
                    }}
                )
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Updated role: {role_data["name"]}'))
            else:
                # Insert new role
                roles_collection.insert_one(role_data)
                inserted_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created role: {role_data["name"]}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Seeding complete! Inserted: {inserted_count}, Updated: {updated_count}'
        ))
