"""
Data models and schema definitions for the CouchDB project
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import uuid

class DataModel:
    """Base data model with common fields"""

    @staticmethod
    def generate_id() -> str:
        """Generate a unique ID"""
        return str(uuid.uuid4())

    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp in ISO format"""
        return datetime.now(timezone.utc).isoformat()

class ProductSchema:
    """Schema for product documents"""

    @staticmethod
    def create_product(name: str, category: str, price: float, description: str = "",
                      status: str = "active", metadata: Dict = None) -> Dict[str, Any]:
        """Create a product document"""
        now = DataModel.get_timestamp()

        return {
            "_id": f"product_{DataModel.generate_id()}",
            "type": "product",
            "name": name,
            "category": category,
            "price": price,
            "description": description,
            "status": status,
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
            "version": 1
        }

class OrderSchema:
    """Schema for order documents"""

    @staticmethod
    def create_order(customer_id: str, products: List[Dict], total: float,
                    status: str = "pending", shipping_address: Dict = None) -> Dict[str, Any]:
        """Create an order document"""
        now = DataModel.get_timestamp()

        return {
            "_id": f"order_{DataModel.generate_id()}",
            "type": "order",
            "customer_id": customer_id,
            "products": products,  # [{"product_id": "...", "quantity": 2, "price": 29.99}]
            "total": total,
            "status": status,
            "shipping_address": shipping_address or {},
            "created_at": now,
            "updated_at": now,
            "version": 1
        }

class CustomerSchema:
    """Schema for customer documents"""

    @staticmethod
    def create_customer(name: str, email: str, phone: str = "",
                       address: Dict = None, metadata: Dict = None) -> Dict[str, Any]:
        """Create a customer document"""
        now = DataModel.get_timestamp()

        return {
            "_id": f"customer_{DataModel.generate_id()}",
            "type": "customer",
            "name": name,
            "email": email,
            "phone": phone,
            "address": address or {},
            "metadata": metadata or {},
            "created_at": now,
            "updated_at": now,
            "version": 1
        }

class AnalyticsEventSchema:
    """Schema for analytics events"""

    @staticmethod
    def create_event(event_type: str, entity_id: str, entity_type: str,
                    event_data: Dict = None, user_id: str = None) -> Dict[str, Any]:
        """Create an analytics event document"""
        now = DataModel.get_timestamp()

        return {
            "_id": f"event_{DataModel.generate_id()}",
            "type": "analytics_event",
            "event_type": event_type,  # "view", "purchase", "add_to_cart", etc.
            "entity_id": entity_id,
            "entity_type": entity_type,  # "product", "order", "customer"
            "event_data": event_data or {},
            "user_id": user_id,
            "timestamp": now,
            "created_at": now,
            "version": 1
        }

# Sample data templates
SAMPLE_PRODUCTS = [
    {
        "name": "Smartphone XY Pro",
        "category": "Electronics",
        "price": 699.99,
        "description": "Latest smartphone with advanced features",
        "metadata": {"brand": "TechCorp", "warranty": "2 years", "color": "Black"}
    },
    {
        "name": "Coffee Maker Deluxe",
        "category": "Home & Kitchen",
        "price": 89.99,
        "description": "Programmable coffee maker with timer",
        "metadata": {"capacity": "12 cups", "material": "Stainless Steel"}
    },
    {
        "name": "Wireless Headphones",
        "category": "Electronics",
        "price": 199.99,
        "description": "Noise-canceling wireless headphones",
        "metadata": {"battery_life": "30 hours", "wireless": True}
    },
    {
        "name": "Yoga Mat Premium",
        "category": "Sports & Fitness",
        "price": 49.99,
        "description": "Non-slip yoga mat with carrying strap",
        "metadata": {"thickness": "6mm", "material": "TPE"}
    },
    {
        "name": "LED Desk Lamp",
        "category": "Home & Kitchen",
        "price": 35.99,
        "description": "Adjustable LED desk lamp with USB charging",
        "metadata": {"power": "12W", "adjustable": True}
    }
]

SAMPLE_CUSTOMERS = [
    {
        "name": "Alice Johnson",
        "email": "alice.johnson@email.com",
        "phone": "+1-555-0101",
        "address": {"street": "123 Main St", "city": "New York", "zip": "10001", "country": "USA"}
    },
    {
        "name": "Bob Smith",
        "email": "bob.smith@email.com",
        "phone": "+1-555-0102",
        "address": {"street": "456 Oak Ave", "city": "Los Angeles", "zip": "90210", "country": "USA"}
    },
    {
        "name": "Carol Davis",
        "email": "carol.davis@email.com",
        "phone": "+1-555-0103",
        "address": {"street": "789 Pine St", "city": "Chicago", "zip": "60601", "country": "USA"}
    }
]