#!/usr/bin/env python3
"""
CouchDB Setup Script
Creates database, users, roles, and Mango indexes
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
import time

load_dotenv()

class CouchDBSetup:
    def __init__(self):
        self.base_url = os.getenv('COUCHDB_URL', 'http://localhost:5984')
        self.admin_user = os.getenv('ADMIN_USER', 'admin')
        self.admin_password = os.getenv('ADMIN_PASSWORD', 'adminpass')
        self.analyst_user = os.getenv('ANALYST_USER', 'analyst')
        self.analyst_password = os.getenv('ANALYST_PASSWORD', 'analyst123')
        self.db_name = os.getenv('DATABASE_NAME', 'tp_database')

        self.session = requests.Session()
        self.session.auth = (self.admin_user, self.admin_password)
        self.session.headers.update({'Content-Type': 'application/json'})

    def check_couchdb_connection(self):
        """Check if CouchDB is running and accessible"""
        try:
            response = self.session.get(self.base_url)
            if response.status_code == 200:
                print("CouchDB is running")
                return True
            else:
                print(f"✗ CouchDB returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("✗ Cannot connect to CouchDB. Make sure it's running on", self.base_url)
            return False

    def setup_cluster(self):
        """Setup CouchDB cluster (single node)"""
        cluster_data = {
            "action": "enable_cluster",
            "bind_address": "0.0.0.0",
            "username": self.admin_user,
            "password": self.admin_password,
            "node_count": "1"
        }

        try:
            response = self.session.post(
                f"{self.base_url}/_cluster_setup",
                data=json.dumps(cluster_data)
            )
            if response.status_code in [200, 201]:
                print("✓ Cluster setup completed")
                return True
            else:
                print(f"Cluster setup response: {response.status_code} - {response.text}")
                return True  # May already be setup
        except Exception as e:
            print(f"Cluster setup info: {e}")
            return True  # Continue anyway

    def create_system_databases(self):
        """Create system databases if they don't exist"""
        system_dbs = ['_users', '_replicator', '_global_changes']
        for db in system_dbs:
            try:
                response = self.session.put(f"{self.base_url}/{db}")
                if response.status_code in [201, 412]:
                    print(f"✓ System database '{db}' ready")
                else:
                    print(f"⚠ System database '{db}': {response.status_code}")
            except Exception as e:
                print(f"⚠ Error with system database '{db}': {e}")
        return True

    def create_database(self):
        """Create the main database"""
        try:
            response = self.session.put(f"{self.base_url}/{self.db_name}")
            if response.status_code == 201:
                print(f"✓ Database '{self.db_name}' created")
                return True
            elif response.status_code == 412:
                print(f"✓ Database '{self.db_name}' already exists")
                return True
            else:
                print(f"✗ Failed to create database: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"✗ Error creating database: {e}")
            return False

    def create_user(self, username, password, roles=None):
        """Create a user with specified roles"""
        if roles is None:
            roles = []

        user_doc = {
            "_id": f"org.couchdb.user:{username}",
            "name": username,
            "password": password,
            "roles": roles,
            "type": "user"
        }

        try:
            response = self.session.put(
                f"{self.base_url}/_users/org.couchdb.user:{username}",
                data=json.dumps(user_doc)
            )
            if response.status_code in [201, 409]:
                print(f"✓ User '{username}' created/exists")
                return True
            else:
                print(f"✗ Failed to create user '{username}': {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"✗ Error creating user '{username}': {e}")
            return False

    def set_database_security(self):
        """Set database security document"""
        security_doc = {
            "admins": {
                "names": [self.admin_user],
                "roles": ["admin"]
            },
            "members": {
                "names": [self.analyst_user],
                "roles": ["analyst", "reader"]
            }
        }

        try:
            response = self.session.put(
                f"{self.base_url}/{self.db_name}/_security",
                data=json.dumps(security_doc)
            )
            if response.status_code == 200:
                print("✓ Database security configured")
                return True
            else:
                print(f"✗ Failed to set security: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"✗ Error setting security: {e}")
            return False

    def create_mango_indexes(self):
        """Create Mango indexes for efficient querying"""
        indexes = [
            {
                "index": {"fields": ["type"]},
                "name": "type-index",
                "type": "json"
            },
            {
                "index": {"fields": ["created_at"]},
                "name": "created_at-index",
                "type": "json"
            },
            {
                "index": {"fields": ["updated_at"]},
                "name": "updated_at-index",
                "type": "json"
            },
            {
                "index": {"fields": ["status"]},
                "name": "status-index",
                "type": "json"
            },
            {
                "index": {"fields": ["type", "status"]},
                "name": "type-status-index",
                "type": "json"
            },
            {
                "index": {"fields": ["category", "created_at"]},
                "name": "category-created-index",
                "type": "json"
            }
        ]

        created_count = 0
        for index_def in indexes:
            try:
                response = self.session.post(
                    f"{self.base_url}/{self.db_name}/_index",
                    data=json.dumps(index_def)
                )
                if response.status_code in [200, 201]:
                    created_count += 1
                    print(f"✓ Index '{index_def['name']}' created")
                else:
                    print(f"✗ Failed to create index '{index_def['name']}': {response.text}")
            except Exception as e:
                print(f"✗ Error creating index '{index_def['name']}': {e}")

        print(f"✓ Created {created_count}/{len(indexes)} indexes")
        return created_count > 0

    def print_curl_commands(self):
        """Print equivalent curl commands for manual setup"""
        print("\n" + "="*50)
        print("ALTERNATIVE: Manual setup using curl commands")
        print("="*50)

        commands = [
            f"# Check CouchDB status",
            f"curl -X GET {self.base_url}",
            f"",
            f"# Create database",
            f"curl -X PUT {self.base_url}/{self.db_name} -u {self.admin_user}:{self.admin_password}",
            f"",
            f"# Create analyst user",
            f"""curl -X PUT {self.base_url}/_users/org.couchdb.user:{self.analyst_user} \\
  -u {self.admin_user}:{self.admin_password} \\
  -H "Content-Type: application/json" \\
  -d '{{"_id": "org.couchdb.user:{self.analyst_user}", "name": "{self.analyst_user}", "password": "{self.analyst_password}", "roles": ["analyst"], "type": "user"}}'""",
            f"",
            f"# Set database security",
            f"""curl -X PUT {self.base_url}/{self.db_name}/_security \\
  -u {self.admin_user}:{self.admin_password} \\
  -H "Content-Type: application/json" \\
  -d '{{"admins": {{"names": ["{self.admin_user}"], "roles": ["admin"]}}, "members": {{"names": ["{self.analyst_user}"], "roles": ["analyst", "reader"]}}}}'""",
            f"",
            f"# Create Mango index (example)",
            f"""curl -X POST {self.base_url}/{self.db_name}/_index \\
  -u {self.admin_user}:{self.admin_password} \\
  -H "Content-Type: application/json" \\
  -d '{{"index": {{"fields": ["type"]}}, "name": "type-index", "type": "json"}}'"""
        ]

        for cmd in commands:
            print(cmd)

    def run_setup(self):
        """Run the complete setup process"""
        print("Starting CouchDB setup...")
        print("-" * 30)

        if not self.check_couchdb_connection():
            print("\nPlease start CouchDB first:")
            print("- On Windows: Start CouchDB service or run 'couchdb' command")
            print("- On Linux/Mac: sudo systemctl start couchdb or brew services start couchdb")
            sys.exit(1)

        # Setup steps
        steps = [
            ("Setting up cluster", self.setup_cluster),
            ("Creating system databases", self.create_system_databases),
            ("Creating database", self.create_database),
            ("Creating admin user", lambda: self.create_user(self.admin_user, self.admin_password, ["admin"])),
            ("Creating analyst user", lambda: self.create_user(self.analyst_user, self.analyst_password, ["analyst"])),
            ("Setting database security", self.set_database_security),
            ("Creating Mango indexes", self.create_mango_indexes)
        ]

        success_count = 0
        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            if step_func():
                success_count += 1
            time.sleep(0.5)  # Small delay between operations

        print(f"\nSetup completed: {success_count}/{len(steps)} steps successful")

        if success_count == len(steps):
            print("\n🎉 CouchDB setup completed successfully!")
            print(f"Database URL: {self.base_url}")
            print(f"Database name: {self.db_name}")
            print(f"Admin user: {self.admin_user}")
            print(f"Analyst user: {self.analyst_user}")
        else:
            print("\n⚠️  Some setup steps failed. Check the errors above.")

        self.print_curl_commands()

if __name__ == "__main__":
    setup = CouchDBSetup()
    setup.run_setup()