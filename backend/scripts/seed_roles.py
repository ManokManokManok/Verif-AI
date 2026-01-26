#!/usr/bin/env python
"""
Script to seed default roles into MongoDB.
Run this script after setting up your environment to create the default roles.
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'verfai.settings')

import django
django.setup()

from src.infrastructure.mongodb.connection import get_mongo_client, get_database_name
from src.infrastructure.mongodb.repositories import MongoDBRoleRepository


def seed_default_roles():
    """Seed default roles into MongoDB."""
    
    # Default roles with permissions
    default_roles = [
        {
            'name': 'admin',
            'permissions': [
                'create_user', 'delete_user', 'update_user',
                'create_post', 'delete_post', 'update_post',
                'view_analytics', 'manage_system'
            ],
            'description': 'System administrator with full access'
        },
        {
            'name': 'moderator',
            'permissions': [
                'create_post', 'delete_post', 'update_post',
                'view_analytics'
            ],
            'description': 'Content moderator with limited admin access'
        },
        {
            'name': 'user',
            'permissions': [
                'create_post', 'update_own_post', 'view_own_profile'
            ],
            'description': 'Regular user with basic permissions'
        }
    ]
    
    try:
        # Initialize repository
        client = get_mongo_client()
        db_name = get_database_name()
        role_repo = MongoDBRoleRepository(client, db_name)
        
        # Create roles
        created_roles = []
        for role_data in default_roles:
            # Check if role already exists
            existing_role = role_repo.get_by_name(role_data['name'])
            if existing_role:
                print(f"Role '{role_data['name']}' already exists, skipping...")
                continue
            
            # Create new role
            from src.domain.entities import Role
            role = Role(
                id=None,
                name=role_data['name'],
                permissions=role_data['permissions'],
                description=role_data['description']
            )
            
            created_role = role_repo.create_role(role)
            created_roles.append(created_role)
            print(f"Created role: {created_role.name}")
        
        print(f"\nSuccessfully created {len(created_roles)} roles:")
        for role in created_roles:
            print(f"  - {role.name}: {len(role.permissions)} permissions")
        
    except Exception as e:
        print(f"Error seeding roles: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    print("Seeding default roles...")
    seed_default_roles()
    print("Done!")
