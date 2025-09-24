#!/usr/bin/env python3
"""
Setup Analytics Views Script
Creates the MapReduce views needed for the dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.analytics import setup_analytics

if __name__ == "__main__":
    print("Setting up analytics views...")
    try:
        engine = setup_analytics()
        print("Analytics views created successfully!")

        # Test the views
        print("\nTesting views...")
        result = engine.get_sales_by_month_mapreduce()
        if result["success"]:
            print(f"Sales by month view working: {len(result.get('rows', []))} results")
        else:
            print(f"Sales by month view failed: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"Failed to setup analytics: {e}")
        sys.exit(1)