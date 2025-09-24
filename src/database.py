"""
CouchDB CRUD operations
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

class CouchDBClient:
    def __init__(self, url: str = None, username: str = None, password: str = None, database: str = None):
        self.base_url = url or os.getenv('COUCHDB_URL', 'http://localhost:5984')
        self.username = username or os.getenv('COUCHDB_USER', 'admin')
        self.password = password or os.getenv('COUCHDB_PASSWORD', 'admin123')
        self.db_name = database or os.getenv('DATABASE_NAME', 'tp_database')

        self.session = requests.Session()
        self.session.auth = (self.username, self.password)
        self.session.headers.update({'Content-Type': 'application/json'})

    def create(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new document in CouchDB

        Args:
            document: Document to create

        Returns:
            Dict containing success status, document ID and revision
        """
        try:
            # Ensure document has required timestamps
            now = datetime.now(timezone.utc).isoformat()
            if 'created_at' not in document:
                document['created_at'] = now
            document['updated_at'] = now

            response = self.session.post(
                f"{self.base_url}/{self.db_name}",
                data=json.dumps(document)
            )

            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "id": result.get('id'),
                    "rev": result.get('rev'),
                    "message": "Document created successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "message": "Failed to create document"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred during document creation"
            }

    def read(self, doc_id: str, include_revs: bool = False) -> Dict[str, Any]:
        """
        Read a document from CouchDB

        Args:
            doc_id: Document ID to retrieve
            include_revs: Whether to include revision history

        Returns:
            Dict containing document data or error information
        """
        try:
            params = {}
            if include_revs:
                params['revs'] = 'true'

            response = self.session.get(
                f"{self.base_url}/{self.db_name}/{doc_id}",
                params=params
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "document": response.json(),
                    "message": "Document retrieved successfully"
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": "Document not found",
                    "message": f"Document with ID '{doc_id}' does not exist"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "message": "Failed to retrieve document"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred during document retrieval"
            }

    def update(self, doc_id: str, updates: Dict[str, Any], merge: bool = True) -> Dict[str, Any]:
        """
        Update an existing document

        Args:
            doc_id: Document ID to update
            updates: Fields to update
            merge: Whether to merge with existing document or replace entirely

        Returns:
            Dict containing success status and new revision
        """
        try:
            # First, get the current document to get its revision
            current_result = self.read(doc_id)
            if not current_result['success']:
                return current_result

            current_doc = current_result['document']

            if merge:
                # Merge updates with existing document
                updated_doc = current_doc.copy()
                updated_doc.update(updates)
            else:
                # Replace document entirely, but keep _id and _rev
                updated_doc = updates.copy()
                updated_doc['_id'] = current_doc['_id']
                updated_doc['_rev'] = current_doc['_rev']

            # Update timestamp
            updated_doc['updated_at'] = datetime.now(timezone.utc).isoformat()

            response = self.session.put(
                f"{self.base_url}/{self.db_name}/{doc_id}",
                data=json.dumps(updated_doc)
            )

            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "id": result.get('id'),
                    "rev": result.get('rev'),
                    "message": "Document updated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "message": "Failed to update document"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred during document update"
            }

    def delete(self, doc_id: str, soft_delete: bool = False) -> Dict[str, Any]:
        """
        Delete a document from CouchDB

        Args:
            doc_id: Document ID to delete
            soft_delete: Whether to soft delete (mark as deleted) or hard delete

        Returns:
            Dict containing success status
        """
        try:
            # Get current document to get revision
            current_result = self.read(doc_id)
            if not current_result['success']:
                return current_result

            current_doc = current_result['document']

            if soft_delete:
                # Soft delete: mark document as deleted
                return self.update(doc_id, {
                    'deleted': True,
                    'deleted_at': datetime.now(timezone.utc).isoformat()
                })
            else:
                # Hard delete: remove document entirely
                response = self.session.delete(
                    f"{self.base_url}/{self.db_name}/{doc_id}",
                    params={'rev': current_doc['_rev']}
                )

                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "id": result.get('id'),
                        "rev": result.get('rev'),
                        "message": "Document deleted successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "message": "Failed to delete document"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred during document deletion"
            }

    def replace(self, doc_id: str, new_document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Replace a document entirely (convenience method for update with merge=False)

        Args:
            doc_id: Document ID to replace
            new_document: New document content

        Returns:
            Dict containing success status
        """
        return self.update(doc_id, new_document, merge=False)

    def find(self, selector: Dict[str, Any], limit: int = 100, skip: int = 0,
             sort: List[Dict[str, str]] = None, fields: List[str] = None) -> Dict[str, Any]:
        """
        Find documents using Mango query

        Args:
            selector: Query selector
            limit: Maximum number of documents to return
            skip: Number of documents to skip
            sort: Sort order
            fields: Fields to return

        Returns:
            Dict containing matching documents
        """
        try:
            query = {
                "selector": selector,
                "limit": limit,
                "skip": skip
            }

            if sort:
                query["sort"] = sort

            if fields:
                query["fields"] = fields

            response = self.session.post(
                f"{self.base_url}/{self.db_name}/_find",
                data=json.dumps(query)
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "documents": result.get('docs', []),
                    "bookmark": result.get('bookmark'),
                    "total_found": len(result.get('docs', [])),
                    "message": "Documents found successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "message": "Failed to execute find query"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred during find operation"
            }

    def bulk_create(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple documents in a single request

        Args:
            documents: List of documents to create

        Returns:
            Dict containing results for each document
        """
        try:
            # Add timestamps to all documents
            now = datetime.now(timezone.utc).isoformat()
            for doc in documents:
                if 'created_at' not in doc:
                    doc['created_at'] = now
                doc['updated_at'] = now

            bulk_data = {"docs": documents}

            response = self.session.post(
                f"{self.base_url}/{self.db_name}/_bulk_docs",
                data=json.dumps(bulk_data)
            )

            if response.status_code == 201:
                results = response.json()
                success_count = sum(1 for r in results if 'ok' in r and r['ok'])

                return {
                    "success": True,
                    "results": results,
                    "total": len(documents),
                    "success_count": success_count,
                    "error_count": len(documents) - success_count,
                    "message": f"Bulk operation completed: {success_count}/{len(documents)} successful"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "message": "Failed to execute bulk create operation"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred during bulk create operation"
            }

    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information and statistics

        Returns:
            Dict containing database info
        """
        try:
            response = self.session.get(f"{self.base_url}/{self.db_name}")

            if response.status_code == 200:
                return {
                    "success": True,
                    "info": response.json(),
                    "message": "Database info retrieved successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "message": "Failed to get database info"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred while getting database info"
            }

# Convenience functions for specific document types
class ProductCRUD:
    def __init__(self, db_client: CouchDBClient):
        self.db = db_client

    def create_product(self, name: str, category: str, price: float, **kwargs) -> Dict[str, Any]:
        from models import ProductSchema
        product = ProductSchema.create_product(name, category, price, **kwargs)
        return self.db.create(product)

    def get_products_by_category(self, category: str) -> Dict[str, Any]:
        return self.db.find({"type": "product", "category": category})

    def get_products_by_price_range(self, min_price: float, max_price: float) -> Dict[str, Any]:
        return self.db.find({
            "type": "product",
            "price": {"$gte": min_price, "$lte": max_price}
        })

class CustomerCRUD:
    def __init__(self, db_client: CouchDBClient):
        self.db = db_client

    def create_customer(self, name: str, email: str, **kwargs) -> Dict[str, Any]:
        from models import CustomerSchema
        customer = CustomerSchema.create_customer(name, email, **kwargs)
        return self.db.create(customer)

    def find_customer_by_email(self, email: str) -> Dict[str, Any]:
        return self.db.find({"type": "customer", "email": email})

class OrderCRUD:
    def __init__(self, db_client: CouchDBClient):
        self.db = db_client

    def create_order(self, customer_id: str, products: List[Dict], total: float, **kwargs) -> Dict[str, Any]:
        from models import OrderSchema
        order = OrderSchema.create_order(customer_id, products, total, **kwargs)
        return self.db.create(order)

    def get_orders_by_status(self, status: str) -> Dict[str, Any]:
        return self.db.find({"type": "order", "status": status})

    def get_customer_orders(self, customer_id: str) -> Dict[str, Any]:
        return self.db.find({"type": "order", "customer_id": customer_id})