#!/usr/bin/env python3
"""
Debug script to check database contents and views
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import CouchDBClient
from src.analytics import AnalyticsEngine

def debug_database():
    # Initialize client
    client = CouchDBClient()

    print("Debugging CouchDB contents...")
    print("-" * 40)

    # Check all documents
    print("1. Checking all documents...")
    result = client.get_all_documents(include_docs=True)
    if result["success"]:
        docs = result["documents"]
        print(f"Total documents: {len(docs)}")

        # Count by type
        type_counts = {}
        for doc in docs:
            doc_type = doc.get("type", "no_type")
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

        print("Documents by type:")
        for doc_type, count in type_counts.items():
            print(f"  {doc_type}: {count}")

    # Check orders specifically
    print("\n2. Checking orders...")
    order_query = {
        "selector": {"type": "order"},
        "fields": ["_id", "type", "total", "created_at", "status"],
        "limit": 5
    }

    result = client.find(**order_query)
    if result["success"]:
        orders = result["documents"]
        print(f"Found {len(orders)} orders")
        if orders:
            print("Sample order:")
            sample_order = orders[0]
            for key, value in sample_order.items():
                print(f"  {key}: {value}")

    # Test the MapReduce view directly
    print("\n3. Testing MapReduce view...")
    analytics = AnalyticsEngine(client)

    # Try to get the view result
    view_result = analytics.query_view("analytics", "sales_by_month", group=True)
    print(f"View result success: {view_result['success']}")
    if view_result["success"]:
        rows = view_result.get("rows", [])
        print(f"View returned {len(rows)} rows")
        if rows:
            print("Sample rows:")
            for row in rows[:3]:
                print(f"  {row}")
    else:
        print(f"View error: {view_result.get('error', 'Unknown error')}")

    # Check if the design document exists
    print("\n4. Checking design document...")
    try:
        design_result = client.session.get(f"{client.base_url}/{client.db_name}/_design/analytics")
        print(f"Design document status: {design_result.status_code}")
        if design_result.status_code == 200:
            design_doc = design_result.json()
            views = design_doc.get("views", {})
            print(f"Views in design document: {list(views.keys())}")
        else:
            print(f"Design document error: {design_result.text}")
    except Exception as e:
        print(f"Error checking design document: {e}")

if __name__ == "__main__":
    debug_database()