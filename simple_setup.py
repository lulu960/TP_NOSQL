#!/usr/bin/env python3
"""
Simple CouchDB Setup Script without Unicode characters
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class SimpleCouchDBSetup:
    def __init__(self):
        self.base_url = os.getenv('COUCHDB_URL', 'http://localhost:5984')
        self.admin_user = os.getenv('ADMIN_USER', 'admin')
        self.admin_password = os.getenv('ADMIN_PASSWORD', 'adminpass')
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
                print(f"CouchDB returned status {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("Cannot connect to CouchDB. Make sure it's running on", self.base_url)
            return False

    def create_database(self):
        """Create the main database"""
        try:
            response = self.session.put(f"{self.base_url}/{self.db_name}")
            if response.status_code == 201:
                print(f"Database '{self.db_name}' created")
                return True
            elif response.status_code == 412:
                print(f"Database '{self.db_name}' already exists")
                return True
            else:
                print(f"Failed to create database: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error creating database: {e}")
            return False

    def run_setup(self):
        """Run the setup process"""
        print("Starting simple CouchDB setup...")
        print("-" * 40)

        if not self.check_couchdb_connection():
            print("\nPlease start CouchDB first:")
            print("- On Windows: Start CouchDB service or run 'couchdb' command")
            print("- On Linux/Mac: sudo systemctl start couchdb or brew services start couchdb")
            sys.exit(1)

        print("\nCreating database...")
        if self.create_database():
            print("Setup completed successfully!")
            print(f"Database URL: {self.base_url}")
            print(f"Database name: {self.db_name}")
        else:
            print("Setup failed. Check the errors above.")
            sys.exit(1)

if __name__ == "__main__":
    setup = SimpleCouchDBSetup()
    setup.run_setup()