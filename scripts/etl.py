#!/usr/bin/env python3
"""
ETL Script for CouchDB Data Processing
Handles data cleaning, enrichment, and importing to CouchDB
"""

import os
import sys
import json
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import time
import random

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from models import ProductSchema, CustomerSchema, OrderSchema, AnalyticsEventSchema, SAMPLE_PRODUCTS, SAMPLE_CUSTOMERS

load_dotenv()

class ETLProcessor:
    def __init__(self):
        self.base_url = os.getenv('COUCHDB_URL', 'http://localhost:5984')
        self.admin_user = os.getenv('ADMIN_USER', 'admin')
        self.admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        self.db_name = os.getenv('DATABASE_NAME', 'tp_database')

        self.session = requests.Session()
        self.session.auth = (self.admin_user, self.admin_password)
        self.session.headers.update({'Content-Type': 'application/json'})

    def clean_text_data(self, text: str) -> str:
        """Clean and normalize text data"""
        if not text or not isinstance(text, str):
            return ""

        # Remove extra whitespace and normalize
        cleaned = ' '.join(text.strip().split())

        # Remove special characters that might cause issues
        cleaned = cleaned.replace('\n', ' ').replace('\r', '').replace('\t', ' ')

        return cleaned

    def validate_email(self, email: str) -> bool:
        """Basic email validation"""
        if not email or '@' not in email:
            return False
        return len(email.split('@')) == 2 and '.' in email.split('@')[1]

    def enrich_product_data(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich product data with calculated fields"""
        enriched = product.copy()

        # Add price category
        price = enriched.get('price', 0)
        if price < 50:
            enriched['price_category'] = 'budget'
        elif price < 200:
            enriched['price_category'] = 'mid-range'
        else:
            enriched['price_category'] = 'premium'

        # Add search keywords
        name = enriched.get('name', '').lower()
        category = enriched.get('category', '').lower()
        description = enriched.get('description', '').lower()

        keywords = set()
        for text in [name, category, description]:
            keywords.update(text.split())

        enriched['search_keywords'] = list(keywords)

        # Add updated timestamp
        enriched['updated_at'] = datetime.now(timezone.utc).isoformat()

        return enriched

    def generate_sample_orders(self, customers: List[Dict], products: List[Dict], count: int = 20) -> List[Dict]:
        """Generate sample orders for testing"""
        orders = []
        statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']

        for i in range(count):
            customer = random.choice(customers)
            num_products = random.randint(1, 4)
            order_products = []
            total = 0

            for _ in range(num_products):
                product = random.choice(products)
                quantity = random.randint(1, 3)
                price = product['price']

                order_products.append({
                    "product_id": product['_id'],
                    "product_name": product['name'],
                    "quantity": quantity,
                    "unit_price": price,
                    "total_price": price * quantity
                })
                total += price * quantity

            order = OrderSchema.create_order(
                customer_id=customer['_id'],
                products=order_products,
                total=round(total, 2),
                status=random.choice(statuses),
                shipping_address=customer.get('address', {})
            )

            # Simulate some orders being older
            if random.random() > 0.3:
                days_ago = random.randint(1, 90)
                old_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
                order['created_at'] = old_date.isoformat()
                order['updated_at'] = old_date.isoformat()

            orders.append(order)

        return orders

    def generate_sample_events(self, customers: List[Dict], products: List[Dict], orders: List[Dict], count: int = 100) -> List[Dict]:
        """Generate sample analytics events"""
        events = []
        event_types = ['product_view', 'add_to_cart', 'remove_from_cart', 'purchase', 'search']

        for i in range(count):
            event_type = random.choice(event_types)
            customer = random.choice(customers)

            if event_type == 'purchase':
                order = random.choice(orders)
                event = AnalyticsEventSchema.create_event(
                    event_type=event_type,
                    entity_id=order['_id'],
                    entity_type='order',
                    event_data={
                        'order_total': order['total'],
                        'product_count': len(order['products'])
                    },
                    user_id=customer['_id']
                )
            else:
                product = random.choice(products)
                event = AnalyticsEventSchema.create_event(
                    event_type=event_type,
                    entity_id=product['_id'],
                    entity_type='product',
                    event_data={
                        'product_name': product['name'],
                        'product_category': product['category'],
                        'product_price': product['price']
                    },
                    user_id=customer['_id']
                )

            # Simulate events at different times
            days_ago = random.randint(0, 30)
            event_date = datetime.now(timezone.utc).replace(hour=random.randint(8, 22))
            event_date = event_date.replace(day=max(1, event_date.day - days_ago))
            event['timestamp'] = event_date.isoformat()
            event['created_at'] = event_date.isoformat()

            events.append(event)

        return events

    def bulk_insert_documents(self, documents: List[Dict]) -> Dict[str, Any]:
        """Insert multiple documents in bulk"""
        if not documents:
            return {"success": 0, "errors": 0}

        bulk_data = {"docs": documents}

        try:
            response = self.session.post(
                f"{self.base_url}/{self.db_name}/_bulk_docs",
                data=json.dumps(bulk_data)
            )

            if response.status_code == 201:
                results = response.json()
                success_count = sum(1 for r in results if 'ok' in r and r['ok'])
                error_count = len(results) - success_count

                return {
                    "success": success_count,
                    "errors": error_count,
                    "details": results
                }
            else:
                print(f"Bulk insert failed: {response.status_code} - {response.text}")
                return {"success": 0, "errors": len(documents)}

        except Exception as e:
            print(f"Error during bulk insert: {e}")
            return {"success": 0, "errors": len(documents)}

    def process_and_load_data(self):
        """Main ETL process"""
        print("Starting ETL process...")
        print("-" * 40)

        # Step 1: Process and clean products
        print("1. Processing products...")
        clean_products = []
        for product_data in SAMPLE_PRODUCTS:
            # Clean data
            product_data['name'] = self.clean_text_data(product_data['name'])
            product_data['description'] = self.clean_text_data(product_data['description'])

            # Create product document
            product = ProductSchema.create_product(**product_data)

            # Enrich with additional fields
            product = self.enrich_product_data(product)

            clean_products.append(product)

        print(f"   Processed {len(clean_products)} products")

        # Step 2: Process and clean customers
        print("2. Processing customers...")
        clean_customers = []
        for customer_data in SAMPLE_CUSTOMERS:
            # Clean data
            customer_data['name'] = self.clean_text_data(customer_data['name'])

            # Validate email
            if not self.validate_email(customer_data['email']):
                print(f"   Warning: Invalid email for {customer_data['name']}")
                continue

            # Create customer document
            customer = CustomerSchema.create_customer(**customer_data)
            clean_customers.append(customer)

        print(f"   Processed {len(clean_customers)} customers")

        # Step 3: Generate orders
        print("3. Generating sample orders...")
        orders = self.generate_sample_orders(clean_customers, clean_products, 25)
        print(f"   Generated {len(orders)} orders")

        # Step 4: Generate analytics events
        print("4. Generating analytics events...")
        events = self.generate_sample_events(clean_customers, clean_products, orders, 150)
        print(f"   Generated {len(events)} events")

        # Step 5: Bulk insert all data
        print("5. Loading data to CouchDB...")
        all_documents = clean_products + clean_customers + orders + events

        result = self.bulk_insert_documents(all_documents)

        print(f"   Inserted {result['success']} documents successfully")
        if result['errors'] > 0:
            print(f"   Failed to insert {result['errors']} documents")

        # Step 6: Generate summary statistics
        print("\n6. Data Summary:")
        print(f"   - Products: {len(clean_products)}")
        print(f"   - Customers: {len(clean_customers)}")
        print(f"   - Orders: {len(orders)}")
        print(f"   - Analytics Events: {len(events)}")
        print(f"   - Total Documents: {len(all_documents)}")

        # Save sample data for reference
        self.save_sample_data({
            'products': clean_products,
            'customers': clean_customers,
            'orders': orders,
            'events': events
        })

        return result

    def save_sample_data(self, data: Dict[str, List]):
        """Save sample data to JSON file for reference"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/sample_data.json', 'w') as f:
                json.dump(data, f, indent=2, default=str)
            print(f"   Sample data saved to data/sample_data.json")
        except Exception as e:
            print(f"   Warning: Could not save sample data: {e}")

    def verify_data_integrity(self):
        """Verify that data was loaded correctly"""
        print("\nVerifying data integrity...")

        queries = [
            ("Products", {"selector": {"type": "product"}}),
            ("Customers", {"selector": {"type": "customer"}}),
            ("Orders", {"selector": {"type": "order"}}),
            ("Events", {"selector": {"type": "analytics_event"}})
        ]

        for name, query in queries:
            try:
                response = self.session.post(
                    f"{self.base_url}/{self.db_name}/_find",
                    data=json.dumps(query)
                )

                if response.status_code == 200:
                    result = response.json()
                    count = len(result.get('docs', []))
                    print(f"   ✓ {name}: {count} documents found")
                else:
                    print(f"   ✗ {name}: Query failed ({response.status_code})")

            except Exception as e:
                print(f"   ✗ {name}: Error during verification ({e})")

def main():
    etl = ETLProcessor()

    try:
        # Run ETL process
        result = etl.process_and_load_data()

        if result['success'] > 0:
            # Verify data
            etl.verify_data_integrity()

            print("\nETL process completed successfully!")
            print(f"Database: {etl.base_url}/{etl.db_name}")
        else:
            print("\nETL process failed - no documents were inserted")

    except KeyboardInterrupt:
        print("\nETL process interrupted by user")
    except Exception as e:
        print(f"\nETL process failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()