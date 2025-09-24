#!/usr/bin/env python3
"""
Test analytics directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import CouchDBClient
from src.analytics import AnalyticsEngine

def test_analytics():
    print("Testing analytics...")
    print("-" * 30)

    # Initialize
    client = CouchDBClient()
    analytics = AnalyticsEngine(client)

    # Test direct Mango query for orders
    print("1. Testing direct order query...")
    orders_query = {
        "selector": {"type": "order"},
        "fields": ["_id", "type", "total", "created_at", "status"],
        "limit": 3
    }

    result = client.find(**orders_query)
    print(f"Order query success: {result['success']}")
    if result["success"]:
        orders = result["documents"]
        print(f"Found {len(orders)} orders")
        for order in orders:
            print(f"  Order {order.get('_id', 'NO_ID')}: total={order.get('total')}, created_at={order.get('created_at')}")
    else:
        print(f"Order query error: {result.get('error')}")

    # Test get_sales_summary
    print("\n2. Testing get_sales_summary...")
    summary_result = analytics.get_sales_summary()
    print(f"Sales summary success: {summary_result['success']}")
    if summary_result["success"]:
        data = summary_result["data"]
        print(f"Sales summary: {data}")
    else:
        print(f"Sales summary error: {summary_result.get('error')}")

    # Test MapReduce view
    print("\n3. Testing MapReduce view...")
    mapreduce_result = analytics.get_sales_by_month_mapreduce()
    print(f"MapReduce success: {mapreduce_result['success']}")
    if mapreduce_result["success"]:
        rows = mapreduce_result.get("rows", [])
        print(f"MapReduce returned {len(rows)} rows")
        for row in rows:
            print(f"  {row}")
    else:
        print(f"MapReduce error: {mapreduce_result.get('error')}")

if __name__ == "__main__":
    test_analytics()