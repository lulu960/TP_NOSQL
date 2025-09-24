"""
Unit tests for CouchDB CRUD operations
"""

import pytest
import os
import sys
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import CouchDBClient, ProductCRUD, CustomerCRUD, OrderCRUD

class TestCouchDBClient:
    """Test CouchDB client CRUD operations"""

    def setup_method(self):
        """Setup test client with mocked session"""
        self.client = CouchDBClient(
            url="http://test:5984",
            username="testuser",
            password="testpass",
            database="testdb"
        )

    @patch('database.requests.Session')
    def test_create_success(self, mock_session):
        """Test successful document creation"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"ok": True, "id": "doc123", "rev": "1-abc"}

        mock_session.return_value.post.return_value = mock_response
        self.client.session = mock_session.return_value

        # Test document
        document = {"name": "Test Product", "price": 99.99}

        # Execute
        result = self.client.create(document)

        # Verify
        assert result["success"] is True
        assert result["id"] == "doc123"
        assert result["rev"] == "1-abc"
        assert "created_at" in document
        assert "updated_at" in document

    @patch('database.requests.Session')
    def test_create_failure(self, mock_session):
        """Test failed document creation"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        mock_session.return_value.post.return_value = mock_response
        self.client.session = mock_session.return_value

        # Execute
        result = self.client.create({"name": "Test"})

        # Verify
        assert result["success"] is False
        assert "HTTP 400" in result["error"]

    @patch('database.requests.Session')
    def test_read_success(self, mock_session):
        """Test successful document read"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "_id": "doc123",
            "_rev": "1-abc",
            "name": "Test Product",
            "price": 99.99
        }

        mock_session.return_value.get.return_value = mock_response
        self.client.session = mock_session.return_value

        # Execute
        result = self.client.read("doc123")

        # Verify
        assert result["success"] is True
        assert result["document"]["_id"] == "doc123"
        assert result["document"]["name"] == "Test Product"

    @patch('database.requests.Session')
    def test_read_not_found(self, mock_session):
        """Test document not found"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Object Not Found"

        mock_session.return_value.get.return_value = mock_response
        self.client.session = mock_session.return_value

        # Execute
        result = self.client.read("nonexistent")

        # Verify
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    @patch('database.requests.Session')
    def test_update_success(self, mock_session):
        """Test successful document update"""
        # Setup mocks for read and update
        mock_read_response = Mock()
        mock_read_response.status_code = 200
        mock_read_response.json.return_value = {
            "_id": "doc123",
            "_rev": "1-abc",
            "name": "Old Name",
            "price": 50.00
        }

        mock_update_response = Mock()
        mock_update_response.status_code = 201
        mock_update_response.json.return_value = {"ok": True, "id": "doc123", "rev": "2-def"}

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_read_response
        mock_session_instance.put.return_value = mock_update_response

        mock_session.return_value = mock_session_instance
        self.client.session = mock_session_instance

        # Execute
        result = self.client.update("doc123", {"name": "New Name"})

        # Verify
        assert result["success"] is True
        assert result["id"] == "doc123"
        assert result["rev"] == "2-def"

    @patch('database.requests.Session')
    def test_delete_hard_success(self, mock_session):
        """Test successful hard delete"""
        # Setup mocks
        mock_read_response = Mock()
        mock_read_response.status_code = 200
        mock_read_response.json.return_value = {
            "_id": "doc123",
            "_rev": "1-abc"
        }

        mock_delete_response = Mock()
        mock_delete_response.status_code = 200
        mock_delete_response.json.return_value = {"ok": True, "id": "doc123", "rev": "2-deleted"}

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_read_response
        mock_session_instance.delete.return_value = mock_delete_response

        mock_session.return_value = mock_session_instance
        self.client.session = mock_session_instance

        # Execute
        result = self.client.delete("doc123", soft_delete=False)

        # Verify
        assert result["success"] is True
        assert result["id"] == "doc123"

    @patch('database.requests.Session')
    def test_find_success(self, mock_session):
        """Test successful find operation"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "docs": [
                {"_id": "doc1", "type": "product", "name": "Product 1"},
                {"_id": "doc2", "type": "product", "name": "Product 2"}
            ],
            "bookmark": "bookmark123"
        }

        mock_session.return_value.post.return_value = mock_response
        self.client.session = mock_session.return_value

        # Execute
        result = self.client.find({"type": "product"})

        # Verify
        assert result["success"] is True
        assert len(result["documents"]) == 2
        assert result["total_found"] == 2
        assert result["bookmark"] == "bookmark123"

    @patch('database.requests.Session')
    def test_bulk_create_success(self, mock_session):
        """Test successful bulk create"""
        # Setup mock
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = [
            {"ok": True, "id": "doc1", "rev": "1-abc"},
            {"ok": True, "id": "doc2", "rev": "1-def"}
        ]

        mock_session.return_value.post.return_value = mock_response
        self.client.session = mock_session.return_value

        # Test documents
        documents = [
            {"name": "Product 1", "price": 10.00},
            {"name": "Product 2", "price": 20.00}
        ]

        # Execute
        result = self.client.bulk_create(documents)

        # Verify
        assert result["success"] is True
        assert result["total"] == 2
        assert result["success_count"] == 2
        assert result["error_count"] == 0


class TestProductCRUD:
    """Test Product CRUD operations"""

    def setup_method(self):
        """Setup test client"""
        self.db_client = CouchDBClient()
        self.product_crud = ProductCRUD(self.db_client)

    @patch.object(CouchDBClient, 'create')
    def test_create_product(self, mock_create):
        """Test product creation"""
        mock_create.return_value = {"success": True, "id": "product123"}

        result = self.product_crud.create_product(
            name="Test Product",
            category="Electronics",
            price=99.99,
            description="A test product"
        )

        assert mock_create.called
        # Verify the document structure passed to create
        call_args = mock_create.call_args[0][0]
        assert call_args["name"] == "Test Product"
        assert call_args["category"] == "Electronics"
        assert call_args["price"] == 99.99
        assert call_args["type"] == "product"

    @patch.object(CouchDBClient, 'find')
    def test_get_products_by_category(self, mock_find):
        """Test getting products by category"""
        mock_find.return_value = {"success": True, "documents": []}

        result = self.product_crud.get_products_by_category("Electronics")

        mock_find.assert_called_with({"type": "product", "category": "Electronics"})

    @patch.object(CouchDBClient, 'find')
    def test_get_products_by_price_range(self, mock_find):
        """Test getting products by price range"""
        mock_find.return_value = {"success": True, "documents": []}

        result = self.product_crud.get_products_by_price_range(10.0, 100.0)

        expected_selector = {
            "type": "product",
            "price": {"$gte": 10.0, "$lte": 100.0}
        }
        mock_find.assert_called_with(expected_selector)


class TestCustomerCRUD:
    """Test Customer CRUD operations"""

    def setup_method(self):
        """Setup test client"""
        self.db_client = CouchDBClient()
        self.customer_crud = CustomerCRUD(self.db_client)

    @patch.object(CouchDBClient, 'create')
    def test_create_customer(self, mock_create):
        """Test customer creation"""
        mock_create.return_value = {"success": True, "id": "customer123"}

        result = self.customer_crud.create_customer(
            name="John Doe",
            email="john@example.com",
            phone="555-1234"
        )

        assert mock_create.called
        call_args = mock_create.call_args[0][0]
        assert call_args["name"] == "John Doe"
        assert call_args["email"] == "john@example.com"
        assert call_args["type"] == "customer"

    @patch.object(CouchDBClient, 'find')
    def test_find_customer_by_email(self, mock_find):
        """Test finding customer by email"""
        mock_find.return_value = {"success": True, "documents": []}

        result = self.customer_crud.find_customer_by_email("john@example.com")

        mock_find.assert_called_with({"type": "customer", "email": "john@example.com"})


class TestOrderCRUD:
    """Test Order CRUD operations"""

    def setup_method(self):
        """Setup test client"""
        self.db_client = CouchDBClient()
        self.order_crud = OrderCRUD(self.db_client)

    @patch.object(CouchDBClient, 'create')
    def test_create_order(self, mock_create):
        """Test order creation"""
        mock_create.return_value = {"success": True, "id": "order123"}

        products = [
            {"product_id": "prod1", "quantity": 2, "price": 50.00}
        ]

        result = self.order_crud.create_order(
            customer_id="customer123",
            products=products,
            total=100.00,
            status="pending"
        )

        assert mock_create.called
        call_args = mock_create.call_args[0][0]
        assert call_args["customer_id"] == "customer123"
        assert call_args["total"] == 100.00
        assert call_args["type"] == "order"

    @patch.object(CouchDBClient, 'find')
    def test_get_orders_by_status(self, mock_find):
        """Test getting orders by status"""
        mock_find.return_value = {"success": True, "documents": []}

        result = self.order_crud.get_orders_by_status("pending")

        mock_find.assert_called_with({"type": "order", "status": "pending"})

    @patch.object(CouchDBClient, 'find')
    def test_get_customer_orders(self, mock_find):
        """Test getting customer orders"""
        mock_find.return_value = {"success": True, "documents": []}

        result = self.order_crud.get_customer_orders("customer123")

        mock_find.assert_called_with({"type": "order", "customer_id": "customer123"})


# Integration test helpers
class TestDatabaseIntegration:
    """Integration tests (require actual CouchDB instance)"""

    @pytest.mark.integration
    def test_full_crud_cycle(self):
        """Test complete CRUD cycle with real database"""
        # Skip if not in integration test mode
        if not os.getenv('RUN_INTEGRATION_TESTS'):
            pytest.skip("Integration tests disabled")

        client = CouchDBClient()

        # Create
        test_doc = {
            "_id": "test_doc_integration",
            "type": "test",
            "name": "Integration Test Doc",
            "value": 42
        }

        create_result = client.create(test_doc)
        assert create_result["success"] is True

        # Read
        read_result = client.read("test_doc_integration")
        assert read_result["success"] is True
        assert read_result["document"]["name"] == "Integration Test Doc"

        # Update
        update_result = client.update("test_doc_integration", {"value": 84})
        assert update_result["success"] is True

        # Verify update
        updated_doc = client.read("test_doc_integration")
        assert updated_doc["document"]["value"] == 84

        # Delete
        delete_result = client.delete("test_doc_integration")
        assert delete_result["success"] is True

        # Verify deletion
        deleted_doc = client.read("test_doc_integration")
        assert deleted_doc["success"] is False


if __name__ == "__main__":
    # Run tests with pytest
    import subprocess
    subprocess.run(["python", "-m", "pytest", __file__, "-v"])