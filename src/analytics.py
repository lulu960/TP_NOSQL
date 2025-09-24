"""
Analytics module with Mango queries and MapReduce views
"""

import os
import sys
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append(os.path.dirname(__file__))
from database import CouchDBClient

load_dotenv()

class AnalyticsEngine:
    """Analytics engine for CouchDB data analysis"""

    def __init__(self, db_client: CouchDBClient = None):
        self.db = db_client or CouchDBClient()
        self.base_url = self.db.base_url
        self.db_name = self.db.db_name
        self.session = self.db.session

    def create_mapreduce_view(self, design_doc_name: str, view_name: str,
                             map_function: str, reduce_function: str = None) -> Dict[str, Any]:
        """
        Create a MapReduce view in CouchDB

        Args:
            design_doc_name: Name of the design document
            view_name: Name of the view
            map_function: JavaScript map function
            reduce_function: JavaScript reduce function (optional)

        Returns:
            Dict containing success status
        """
        view_definition = {
            "map": map_function
        }

        if reduce_function:
            view_definition["reduce"] = reduce_function

        design_doc = {
            "_id": f"_design/{design_doc_name}",
            "views": {
                view_name: view_definition
            }
        }

        try:
            # Try to get existing design document
            existing_result = self.db.read(f"_design/{design_doc_name}")
            if existing_result["success"]:
                # Update existing document
                existing_doc = existing_result["document"]
                existing_doc["views"][view_name] = view_definition
                design_doc = existing_doc

            response = self.session.put(
                f"{self.base_url}/{self.db_name}/_design/{design_doc_name}",
                data=json.dumps(design_doc)
            )

            if response.status_code in [201, 200]:
                return {
                    "success": True,
                    "message": f"View '{view_name}' created/updated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "message": "Failed to create view"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred while creating view"
            }

    def query_view(self, design_doc: str, view_name: str, **params) -> Dict[str, Any]:
        """
        Query a MapReduce view

        Args:
            design_doc: Design document name
            view_name: View name
            **params: Query parameters (group, startkey, endkey, etc.)

        Returns:
            Dict containing view results
        """
        try:
            response = self.session.get(
                f"{self.base_url}/{self.db_name}/_design/{design_doc}/_view/{view_name}",
                params=params
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json(),
                    "message": "View queried successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "message": "Failed to query view"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred while querying view"
            }

    def setup_analytics_views(self):
        """Create standard analytics views"""
        views_to_create = [
            {
                "design_doc": "analytics",
                "view_name": "sales_by_month",
                "map_function": """
                function(doc) {
                    if (doc.type === 'order' && doc.created_at && doc.total) {
                        var date = new Date(doc.created_at);
                        var monthKey = [date.getFullYear(), date.getMonth() + 1];
                        emit(monthKey, {
                            total: doc.total,
                            count: 1,
                            status: doc.status
                        });
                    }
                }
                """,
                "reduce_function": """
                function(keys, values, rereduce) {
                    var result = {
                        total: 0,
                        count: 0,
                        delivered: 0,
                        pending: 0,
                        cancelled: 0
                    };

                    for (var i = 0; i < values.length; i++) {
                        var value = values[i];
                        if (rereduce) {
                            result.total += value.total || 0;
                            result.count += value.count || 0;
                            result.delivered += value.delivered || 0;
                            result.pending += value.pending || 0;
                            result.cancelled += value.cancelled || 0;
                        } else {
                            result.total += value.total || 0;
                            result.count += 1;
                            if (value.status === 'delivered') result.delivered++;
                            if (value.status === 'pending') result.pending++;
                            if (value.status === 'cancelled') result.cancelled++;
                        }
                    }

                    return result;
                }
                """
            },
            {
                "design_doc": "analytics",
                "view_name": "products_by_category",
                "map_function": """
                function(doc) {
                    if (doc.type === 'product' && doc.category && doc.price) {
                        emit(doc.category, {
                            count: 1,
                            total_value: doc.price,
                            avg_price: doc.price,
                            product_name: doc.name
                        });
                    }
                }
                """,
                "reduce_function": """
                function(keys, values, rereduce) {
                    var result = {
                        count: 0,
                        total_value: 0,
                        avg_price: 0
                    };

                    for (var i = 0; i < values.length; i++) {
                        var value = values[i];
                        result.count += (rereduce ? value.count : 1);
                        result.total_value += (value.total_value || value.avg_price || 0);
                    }

                    result.avg_price = result.count > 0 ? result.total_value / result.count : 0;
                    return result;
                }
                """
            }
        ]

        results = []
        for view_def in views_to_create:
            result = self.create_mapreduce_view(
                view_def["design_doc"],
                view_def["view_name"],
                view_def["map_function"],
                view_def.get("reduce_function")
            )
            results.append((view_def["view_name"], result))
            print(f"View '{view_def['view_name']}': {'OK' if result['success'] else 'FAIL'} {result['message']}")

        return results

    # Mango Query Examples
    def get_sales_summary(self) -> Dict[str, Any]:
        """Get overall sales summary using Mango queries"""
        # Get all orders
        orders_query = {
            "selector": {"type": "order"},
            "fields": ["total", "status", "created_at", "products"]
        }

        result = self.db.find(**orders_query)
        if not result["success"]:
            return result

        orders = result["documents"]

        # Calculate summary statistics
        total_orders = len(orders)
        total_revenue = sum(order.get("total", 0) for order in orders)

        status_counts = {}
        for order in orders:
            status = order.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

        return {
            "success": True,
            "data": {
                "total_orders": total_orders,
                "total_revenue": round(total_revenue, 2),
                "average_order_value": round(avg_order_value, 2),
                "orders_by_status": status_counts
            },
            "message": "Sales summary calculated successfully"
        }

    def get_top_products(self, limit: int = 10) -> Dict[str, Any]:
        """Get top products by order frequency using Mango queries"""
        # Get all orders with products
        orders_query = {
            "selector": {"type": "order"},
            "fields": ["products"]
        }

        result = self.db.find(**orders_query)
        if not result["success"]:
            return result

        orders = result["documents"]

        # Count product occurrences
        product_counts = {}
        for order in orders:
            for product in order.get("products", []):
                product_id = product.get("product_id", "unknown")
                product_name = product.get("product_name", "Unknown Product")
                quantity = product.get("quantity", 1)

                if product_id not in product_counts:
                    product_counts[product_id] = {
                        "name": product_name,
                        "total_quantity": 0,
                        "order_count": 0
                    }

                product_counts[product_id]["total_quantity"] += quantity
                product_counts[product_id]["order_count"] += 1

        # Sort by total quantity and limit
        sorted_products = sorted(
            [(pid, data) for pid, data in product_counts.items()],
            key=lambda x: x[1]["total_quantity"],
            reverse=True
        )[:limit]

        return {
            "success": True,
            "data": sorted_products,
            "message": f"Top {len(sorted_products)} products retrieved"
        }

    def get_customer_analytics(self) -> Dict[str, Any]:
        """Get customer analytics using Mango queries"""
        # Get all customers
        customers_result = self.db.find({"type": "customer"})
        if not customers_result["success"]:
            return customers_result

        # Get all orders
        orders_result = self.db.find({"type": "order"})
        if not orders_result["success"]:
            return orders_result

        customers = customers_result["documents"]
        orders = orders_result["documents"]

        # Calculate customer metrics
        customer_metrics = {}
        for customer in customers:
            customer_id = customer.get("_id")
            customer_metrics[customer_id] = {
                "name": customer.get("name", "Unknown"),
                "email": customer.get("email", ""),
                "total_orders": 0,
                "total_spent": 0,
                "last_order_date": None
            }

        # Aggregate order data by customer
        for order in orders:
            customer_id = order.get("customer_id")
            if customer_id in customer_metrics:
                customer_metrics[customer_id]["total_orders"] += 1
                customer_metrics[customer_id]["total_spent"] += order.get("total", 0)

                order_date = order.get("created_at")
                if order_date:
                    if (not customer_metrics[customer_id]["last_order_date"] or
                        order_date > customer_metrics[customer_id]["last_order_date"]):
                        customer_metrics[customer_id]["last_order_date"] = order_date

        # Calculate additional metrics
        total_customers = len(customers)
        active_customers = sum(1 for m in customer_metrics.values() if m["total_orders"] > 0)
        avg_orders_per_customer = sum(m["total_orders"] for m in customer_metrics.values()) / total_customers if total_customers > 0 else 0

        return {
            "success": True,
            "data": {
                "total_customers": total_customers,
                "active_customers": active_customers,
                "average_orders_per_customer": round(avg_orders_per_customer, 2),
                "customer_details": list(customer_metrics.values())
            },
            "message": "Customer analytics calculated successfully"
        }

    def get_product_performance(self) -> Dict[str, Any]:
        """Get product performance metrics using Mango queries"""
        # Get all products
        products_result = self.db.find({"type": "product"})
        if not products_result["success"]:
            return products_result

        products = products_result["documents"]

        # Get category distribution
        category_counts = {}
        total_products = len(products)

        for product in products:
            category = product.get("category", "Unknown")
            category_counts[category] = category_counts.get(category, 0) + 1

        # Calculate price statistics
        prices = [p.get("price", 0) for p in products if p.get("price")]
        if prices:
            min_price = min(prices)
            max_price = max(prices)
            avg_price = sum(prices) / len(prices)
        else:
            min_price = max_price = avg_price = 0

        return {
            "success": True,
            "data": {
                "total_products": total_products,
                "categories": category_counts,
                "price_stats": {
                    "min_price": min_price,
                    "max_price": max_price,
                    "average_price": round(avg_price, 2)
                }
            },
            "message": "Product performance metrics calculated"
        }

    def get_recent_activity(self, days: int = 7) -> Dict[str, Any]:
        """Get recent activity using date-based Mango queries"""
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()

        # Query for recent orders
        recent_orders_query = {
            "selector": {
                "type": "order",
                "created_at": {
                    "$gte": start_date_str,
                    "$lte": end_date_str
                }
            }
        }

        orders_result = self.db.find(**recent_orders_query)
        if not orders_result["success"]:
            return orders_result

        # Query for recent analytics events
        recent_events_query = {
            "selector": {
                "type": "analytics_event",
                "timestamp": {
                    "$gte": start_date_str,
                    "$lte": end_date_str
                }
            }
        }

        events_result = self.db.find(**recent_events_query)

        recent_orders = orders_result.get("documents", [])
        recent_events = events_result.get("documents", []) if events_result.get("success") else []

        # Aggregate recent activity
        activity_summary = {
            "period_days": days,
            "total_orders": len(recent_orders),
            "total_events": len(recent_events),
            "orders": recent_orders,
            "events": recent_events[:20]  # Limit events for display
        }

        return {
            "success": True,
            "data": activity_summary,
            "message": f"Recent activity for last {days} days retrieved"
        }

    def get_sales_by_month_mapreduce(self) -> Dict[str, Any]:
        """Get sales by month using MapReduce view"""
        result = self.query_view("analytics", "sales_by_month", group=True)
        if result["success"] and "data" in result:
            # Flatten the structure to match expected format
            return {
                "success": True,
                "rows": result["data"].get("rows", []),
                "message": result["message"]
            }
        return result

    def get_products_by_category_mapreduce(self) -> Dict[str, Any]:
        """Get products by category using MapReduce view"""
        return self.query_view("analytics", "products_by_category", group=True)


# Convenience functions for common analytics operations
def setup_analytics(db_client: CouchDBClient = None) -> AnalyticsEngine:
    """Setup analytics engine and create views"""
    engine = AnalyticsEngine(db_client)
    print("Setting up analytics views...")
    engine.setup_analytics_views()
    return engine

def run_sample_analytics():
    """Run sample analytics queries"""
    print("Running sample analytics...")
    print("-" * 40)

    engine = AnalyticsEngine()

    # Test basic analytics
    queries = [
        ("Sales Summary", engine.get_sales_summary),
        ("Top Products", engine.get_top_products),
        ("Customer Analytics", engine.get_customer_analytics),
        ("Product Performance", engine.get_product_performance),
        ("Recent Activity (7 days)", engine.get_recent_activity)
    ]

    for name, query_func in queries:
        print(f"\n{name}:")
        try:
            result = query_func()
            if result["success"]:
                print(f"  ✓ {result['message']}")
                # Print sample data (limited)
                data = result.get("data", {})
                if isinstance(data, dict):
                    for key, value in list(data.items())[:3]:  # Show first 3 items
                        print(f"    {key}: {value}")
                else:
                    print(f"    Data type: {type(data)}")
            else:
                print(f"  ✗ {result.get('message', 'Query failed')}")
        except Exception as e:
            print(f"  ✗ Error: {e}")

    # Test MapReduce views
    print(f"\nMapReduce Views:")
    mapreduce_queries = [
        ("Sales by Month", engine.get_sales_by_month_mapreduce),
        ("Products by Category", engine.get_products_by_category_mapreduce)
    ]

    for name, query_func in mapreduce_queries:
        print(f"\n{name}:")
        try:
            result = query_func()
            if result["success"]:
                rows = result["data"].get("rows", [])
                print(f"  ✓ Retrieved {len(rows)} rows")
                # Show sample rows
                for row in rows[:3]:
                    print(f"    {row.get('key', 'N/A')}: {row.get('value', 'N/A')}")
            else:
                print(f"  ✗ {result.get('message', 'Query failed')}")
        except Exception as e:
            print(f"  ✗ Error: {e}")


if __name__ == "__main__":
    run_sample_analytics()