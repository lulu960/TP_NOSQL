#!/usr/bin/env python3
"""
Admin and security management scripts for CouchDB
"""

import os
import sys
import json
import csv
import requests
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from database import CouchDBClient

load_dotenv()

class CouchDBAdmin:
    """CouchDB administration utilities"""

    def __init__(self):
        self.base_url = os.getenv('COUCHDB_URL', 'http://localhost:5984')
        self.admin_user = os.getenv('ADMIN_USER', 'admin')
        self.admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        self.db_name = os.getenv('DATABASE_NAME', 'tp_database')

        self.session = requests.Session()
        self.session.auth = (self.admin_user, self.admin_password)
        self.session.headers.update({'Content-Type': 'application/json'})

        self.client = CouchDBClient()

    def create_admin_user(self, username: str, password: str) -> Dict[str, Any]:
        """Create an admin user"""
        user_doc = {
            "_id": f"org.couchdb.user:{username}",
            "name": username,
            "password": password,
            "roles": ["admin", "_admin"],
            "type": "user"
        }

        try:
            response = self.session.put(
                f"{self.base_url}/_users/org.couchdb.user:{username}",
                data=json.dumps(user_doc)
            )

            if response.status_code in [201, 409]:  # 409 = already exists
                return {
                    "success": True,
                    "message": f"Admin user '{username}' created/updated"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "message": f"Failed to create admin user '{username}'"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception creating admin user '{username}'"
            }

    def create_analyst_role(self, username: str, password: str) -> Dict[str, Any]:
        """Create an analyst user with read-only permissions"""
        user_doc = {
            "_id": f"org.couchdb.user:{username}",
            "name": username,
            "password": password,
            "roles": ["analyst", "reader"],
            "type": "user"
        }

        try:
            response = self.session.put(
                f"{self.base_url}/_users/org.couchdb.user:{username}",
                data=json.dumps(user_doc)
            )

            if response.status_code in [201, 409]:  # 409 = already exists
                # Update database security to include analyst
                security_result = self.update_database_security()
                return {
                    "success": True,
                    "message": f"Analyst user '{username}' created/updated",
                    "security_update": security_result
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "message": f"Failed to create analyst user '{username}'"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception creating analyst user '{username}'"
            }

    def update_database_security(self) -> Dict[str, Any]:
        """Update database security settings"""
        security_doc = {
            "admins": {
                "names": [self.admin_user],
                "roles": ["admin", "_admin"]
            },
            "members": {
                "names": [os.getenv('ANALYST_USER', 'analyst')],
                "roles": ["analyst", "reader"]
            }
        }

        try:
            response = self.session.put(
                f"{self.base_url}/{self.db_name}/_security",
                data=json.dumps(security_doc)
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Database security updated"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "message": "Failed to update database security"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Exception updating database security"
            }

    def export_data(self, output_file: str, format: str = 'json', doc_type: Optional[str] = None,
                   batch_size: int = 1000) -> Dict[str, Any]:
        """
        Export data in JSON or CSV format

        Args:
            output_file: Output file path
            format: 'json' or 'csv'
            doc_type: Filter by document type (optional)
            batch_size: Number of documents per batch
        """
        try:
            print(f"Starting export to {output_file} (format: {format})")

            # Build selector
            selector = {}
            if doc_type:
                selector["type"] = doc_type

            # Get total document count first
            count_result = self.client.find(selector, limit=1)
            if not count_result["success"]:
                return {
                    "success": False,
                    "error": count_result.get("error", "Failed to count documents"),
                    "message": "Could not determine document count"
                }

            all_documents = []
            skip = 0
            processed = 0

            print(f"Exporting documents (batch size: {batch_size})")

            # Fetch documents in batches
            while True:
                result = self.client.find(selector, limit=batch_size, skip=skip)

                if not result["success"]:
                    return {
                        "success": False,
                        "error": result.get("error", "Query failed"),
                        "message": f"Failed to fetch batch starting at {skip}"
                    }

                documents = result["documents"]
                if not documents:
                    break

                all_documents.extend(documents)
                processed += len(documents)
                skip += batch_size

                print(f"  Processed: {processed} documents...")

                # If we got fewer documents than batch_size, we're done
                if len(documents) < batch_size:
                    break

            if not all_documents:
                return {
                    "success": False,
                    "message": "No documents found to export"
                }

            # Export based on format
            if format.lower() == 'json':
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(all_documents, f, indent=2, default=str, ensure_ascii=False)

            elif format.lower() == 'csv':
                if not all_documents:
                    return {
                        "success": False,
                        "message": "No documents to export to CSV"
                    }

                # Get all unique keys from documents
                all_keys = set()
                for doc in all_documents:
                    all_keys.update(doc.keys())

                all_keys = sorted(list(all_keys))

                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=all_keys)
                    writer.writeheader()

                    for doc in all_documents:
                        # Convert nested objects to JSON strings for CSV
                        row = {}
                        for key in all_keys:
                            value = doc.get(key, '')
                            if isinstance(value, (dict, list)):
                                value = json.dumps(value, default=str)
                            row[key] = value
                        writer.writerow(row)

            else:
                return {
                    "success": False,
                    "error": f"Unsupported format: {format}",
                    "message": "Format must be 'json' or 'csv'"
                }

            return {
                "success": True,
                "message": f"Exported {len(all_documents)} documents to {output_file}",
                "document_count": len(all_documents)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception during export: {e}"
            }

    def import_data(self, input_file: str, format: str = 'json',
                   batch_size: int = 1000, update_existing: bool = False) -> Dict[str, Any]:
        """
        Import data from JSON or CSV file

        Args:
            input_file: Input file path
            format: 'json' or 'csv'
            batch_size: Number of documents per batch
            update_existing: Whether to update existing documents
        """
        try:
            print(f"Starting import from {input_file} (format: {format})")

            if not os.path.exists(input_file):
                return {
                    "success": False,
                    "error": "File not found",
                    "message": f"Input file '{input_file}' does not exist"
                }

            documents = []

            # Load documents based on format
            if format.lower() == 'json':
                with open(input_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        documents = data
                    else:
                        documents = [data]

            elif format.lower() == 'csv':
                with open(input_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Convert JSON strings back to objects
                        doc = {}
                        for key, value in row.items():
                            if value and value.startswith(('{', '[')):
                                try:
                                    doc[key] = json.loads(value)
                                except json.JSONDecodeError:
                                    doc[key] = value
                            else:
                                doc[key] = value
                        documents.append(doc)

            else:
                return {
                    "success": False,
                    "error": f"Unsupported format: {format}",
                    "message": "Format must be 'json' or 'csv'"
                }

            if not documents:
                return {
                    "success": False,
                    "message": "No documents found in input file"
                }

            print(f"Found {len(documents)} documents to import")

            # Process documents to ensure they have required fields
            now = datetime.now(timezone.utc).isoformat()
            for doc in documents:
                if 'created_at' not in doc:
                    doc['created_at'] = now
                doc['updated_at'] = now

                # If update_existing is False, remove _rev to avoid conflicts
                if not update_existing and '_rev' in doc:
                    del doc['_rev']

            # Import in batches
            total_success = 0
            total_errors = 0

            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                print(f"  Importing batch {i//batch_size + 1}: {len(batch)} documents...")

                result = self.client.bulk_create(batch)

                if result["success"]:
                    total_success += result["success_count"]
                    total_errors += result["error_count"]
                else:
                    total_errors += len(batch)
                    print(f"    Batch failed: {result.get('error', 'Unknown error')}")

            return {
                "success": total_success > 0,
                "message": f"Import completed: {total_success} successful, {total_errors} errors",
                "success_count": total_success,
                "error_count": total_errors,
                "total_documents": len(documents)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception during import: {e}"
            }

    def backup_database(self, backup_file: str) -> Dict[str, Any]:
        """Create a complete database backup"""
        print(f"Creating database backup: {backup_file}")

        # Export all documents
        result = self.export_data(backup_file, format='json')

        if result["success"]:
            # Add metadata
            backup_metadata = {
                "backup_date": datetime.now(timezone.utc).isoformat(),
                "database_name": self.db_name,
                "document_count": result["document_count"],
                "couchdb_url": self.base_url
            }

            # Create metadata file
            metadata_file = backup_file.replace('.json', '_metadata.json')
            with open(metadata_file, 'w') as f:
                json.dump(backup_metadata, f, indent=2)

            return {
                "success": True,
                "message": f"Database backup created: {backup_file}",
                "metadata_file": metadata_file,
                "document_count": result["document_count"]
            }
        else:
            return result

    def restore_database(self, backup_file: str, confirm: bool = False) -> Dict[str, Any]:
        """Restore database from backup"""
        if not confirm:
            return {
                "success": False,
                "message": "Database restore requires confirmation (use --confirm flag)"
            }

        print(f"Restoring database from: {backup_file}")
        print("⚠️  WARNING: This will replace all existing data!")

        # Import data
        result = self.import_data(backup_file, format='json', update_existing=True)

        if result["success"]:
            return {
                "success": True,
                "message": f"Database restored from {backup_file}",
                "imported_documents": result["success_count"]
            }
        else:
            return result

    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            # Basic database info
            db_info = self.client.get_database_info()
            if not db_info["success"]:
                return db_info

            stats = {
                "database_info": db_info["info"],
                "document_types": {},
                "total_documents": 0
            }

            # Count documents by type
            doc_types = ["product", "customer", "order", "analytics_event"]

            for doc_type in doc_types:
                result = self.client.find({"type": doc_type}, limit=1)
                if result["success"]:
                    # Get count (this is approximate since CouchDB doesn't provide exact counts easily)
                    count_result = self.client.find({"type": doc_type}, limit=10000)
                    if count_result["success"]:
                        count = len(count_result["documents"])
                        stats["document_types"][doc_type] = count
                        stats["total_documents"] += count

            return {
                "success": True,
                "data": stats,
                "message": "Database statistics retrieved"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get database statistics"
            }

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='CouchDB Administration Tools')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create admin user
    admin_parser = subparsers.add_parser('create-admin', help='Create admin user')
    admin_parser.add_argument('username', help='Username for admin')
    admin_parser.add_argument('password', help='Password for admin')

    # Create analyst user
    analyst_parser = subparsers.add_parser('create-analyst', help='Create analyst user')
    analyst_parser.add_argument('username', help='Username for analyst')
    analyst_parser.add_argument('password', help='Password for analyst')

    # Export data
    export_parser = subparsers.add_parser('export', help='Export data')
    export_parser.add_argument('output_file', help='Output file path')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Output format')
    export_parser.add_argument('--type', help='Document type to export (optional)')
    export_parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for export')

    # Import data
    import_parser = subparsers.add_parser('import', help='Import data')
    import_parser.add_argument('input_file', help='Input file path')
    import_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Input format')
    import_parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for import')
    import_parser.add_argument('--update', action='store_true', help='Update existing documents')

    # Backup
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('backup_file', help='Backup file path')

    # Restore
    restore_parser = subparsers.add_parser('restore', help='Restore database from backup')
    restore_parser.add_argument('backup_file', help='Backup file path')
    restore_parser.add_argument('--confirm', action='store_true', help='Confirm restoration')

    # Statistics
    subparsers.add_parser('stats', help='Show database statistics')

    # Security update
    subparsers.add_parser('update-security', help='Update database security settings')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    admin = CouchDBAdmin()

    if args.command == 'create-admin':
        result = admin.create_admin_user(args.username, args.password)
        print(f"✓ {result['message']}" if result['success'] else f"✗ {result['message']}")

    elif args.command == 'create-analyst':
        result = admin.create_analyst_role(args.username, args.password)
        print(f"✓ {result['message']}" if result['success'] else f"✗ {result['message']}")

    elif args.command == 'export':
        result = admin.export_data(args.output_file, args.format, args.type, args.batch_size)
        print(f"✓ {result['message']}" if result['success'] else f"✗ {result['message']}")

    elif args.command == 'import':
        result = admin.import_data(args.input_file, args.format, args.batch_size, args.update)
        print(f"✓ {result['message']}" if result['success'] else f"✗ {result['message']}")

    elif args.command == 'backup':
        result = admin.backup_database(args.backup_file)
        print(f"✓ {result['message']}" if result['success'] else f"✗ {result['message']}")

    elif args.command == 'restore':
        result = admin.restore_database(args.backup_file, args.confirm)
        print(f"✓ {result['message']}" if result['success'] else f"✗ {result['message']}")

    elif args.command == 'stats':
        result = admin.get_database_stats()
        if result['success']:
            stats = result['data']
            print("Database Statistics:")
            print(f"  Total Documents: {stats['total_documents']}")
            print("  Documents by Type:")
            for doc_type, count in stats['document_types'].items():
                print(f"    {doc_type}: {count}")

            db_info = stats['database_info']
            print(f"  Database Size: {db_info.get('data_size', 0) / 1024 / 1024:.2f} MB")
            print(f"  Disk Size: {db_info.get('disk_size', 0) / 1024 / 1024:.2f} MB")
        else:
            print(f"✗ {result['message']}")

    elif args.command == 'update-security':
        result = admin.update_database_security()
        print(f"✓ {result['message']}" if result['success'] else f"✗ {result['message']}")

if __name__ == "__main__":
    main()