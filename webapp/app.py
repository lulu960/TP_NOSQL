"""
Streamlit Web Application for CouchDB Analytics Dashboard
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from datetime import datetime, timedelta
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from database import CouchDBClient
from analytics import AnalyticsEngine
from models import ProductSchema, CustomerSchema, OrderSchema, AnalyticsEventSchema

# Page config
st.set_page_config(
    page_title="CouchDB Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2rem;
    font-weight: bold;
    color: #1f77b4;
    margin-bottom: 1rem;
}
.metric-container {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
.success-message {
    color: #28a745;
    font-weight: bold;
}
.error-message {
    color: #dc3545;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_database_connection():
    """Get database connection with caching"""
    try:
        client = CouchDBClient()
        analytics = AnalyticsEngine(client)

        # Test connection
        info = client.get_database_info()
        if info["success"]:
            return client, analytics, None
        else:
            return None, None, info["error"]
    except Exception as e:
        return None, None, str(e)

@st.cache_data(ttl=300)
def load_sales_data(_analytics_engine):
    """Load sales data with caching"""
    if not _analytics_engine:
        return None, "No analytics engine available"

    result = _analytics_engine.get_sales_summary()
    if result["success"]:
        return result["data"], None
    else:
        return None, result.get("error", "Failed to load sales data")

@st.cache_data(ttl=300)
def load_product_data(_analytics_engine):
    """Load product data with caching"""
    if not _analytics_engine:
        return None, "No analytics engine available"

    result = _analytics_engine.get_product_performance()
    if result["success"]:
        return result["data"], None
    else:
        return None, result.get("error", "Failed to load product data")

@st.cache_data(ttl=300)
def load_customer_data(_analytics_engine):
    """Load customer data with caching"""
    if not _analytics_engine:
        return None, "No analytics engine available"

    result = _analytics_engine.get_customer_analytics()
    if result["success"]:
        return result["data"], None
    else:
        return None, result.get("error", "Failed to load customer data")

@st.cache_data(ttl=300)
def load_top_products(_analytics_engine, limit=10):
    """Load top products data"""
    if not _analytics_engine:
        return None, "No analytics engine available"

    result = _analytics_engine.get_top_products(limit)
    if result["success"]:
        return result["data"], None
    else:
        return None, result.get("error", "Failed to load top products")

@st.cache_data(ttl=300)
def load_sales_by_month(_analytics_engine):
    """Load sales by month using MapReduce"""
    if not _analytics_engine:
        return None, "No analytics engine available"

    result = _analytics_engine.get_sales_by_month_mapreduce()
    if result["success"]:
        return result, None
    else:
        return None, result.get("error", "Failed to load sales by month")

def create_kpi_cards(sales_data, customer_data, product_data):
    """Create KPI cards display"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Total Orders",
            value=sales_data.get("total_orders", 0),
            delta=f"+{sales_data.get('total_orders', 0) - 20}"  # Mock delta
        )

    with col2:
        st.metric(
            label="Total Revenue",
            value=f"${sales_data.get('total_revenue', 0):,.2f}",
            delta=f"+{sales_data.get('total_revenue', 0) * 0.1:.2f}"  # Mock 10% increase
        )

    with col3:
        st.metric(
            label="Average Order Value",
            value=f"${sales_data.get('average_order_value', 0):.2f}",
            delta=f"+{sales_data.get('average_order_value', 0) * 0.05:.2f}"  # Mock 5% increase
        )

    with col4:
        st.metric(
            label="Total Customers",
            value=customer_data.get("total_customers", 0),
            delta=f"+{customer_data.get('active_customers', 0) - customer_data.get('total_customers', 0) + 5}"  # Mock delta
        )

def create_order_status_chart(sales_data):
    """Create order status distribution chart"""
    orders_by_status = sales_data.get("orders_by_status", {})

    if not orders_by_status:
        st.warning("No order status data available")
        return

    # Create pie chart
    fig = px.pie(
        values=list(orders_by_status.values()),
        names=list(orders_by_status.keys()),
        title="Order Status Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )

    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )

    fig.update_layout(
        showlegend=True,
        height=400,
        font=dict(size=12)
    )

    st.plotly_chart(fig, use_container_width=True)

def create_product_category_chart(product_data):
    """Create product category distribution chart"""
    categories = product_data.get("categories", {})

    if not categories:
        st.warning("No product category data available")
        return

    # Create bar chart
    fig = px.bar(
        x=list(categories.keys()),
        y=list(categories.values()),
        title="Products by Category",
        labels={'x': 'Category', 'y': 'Number of Products'},
        color=list(categories.values()),
        color_continuous_scale='viridis'
    )

    fig.update_traces(
        hovertemplate='<b>%{x}</b><br>Products: %{y}<extra></extra>'
    )

    fig.update_layout(
        showlegend=False,
        height=400,
        xaxis_tickangle=-45
    )

    st.plotly_chart(fig, use_container_width=True)

def create_sales_trend_chart(sales_by_month_data):
    """Create sales trend chart from MapReduce data"""
    if not sales_by_month_data or "rows" not in sales_by_month_data:
        st.warning("No sales trend data available")
        return

    rows = sales_by_month_data["rows"]
    if not rows:
        st.warning("No sales data found")
        return

    # Process MapReduce results
    months = []
    totals = []
    counts = []

    for row in rows:
        key = row.get("key", [])  # [year, month]
        value = row.get("value", {})

        if len(key) >= 2:
            year, month = key[0], key[1]
            month_str = f"{year}-{month:02d}"
            months.append(month_str)
            totals.append(value.get("total", 0))
            counts.append(value.get("count", 0))

    if not months:
        st.warning("No valid sales data found")
        return

    # Create dual-axis chart
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
        subplot_titles=["Sales Trend Over Time"]
    )

    # Add revenue line
    fig.add_trace(
        go.Scatter(
            x=months,
            y=totals,
            name="Revenue ($)",
            line=dict(color="#1f77b4", width=3),
            hovertemplate='<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>'
        ),
        secondary_y=False,
    )

    # Add order count bars
    fig.add_trace(
        go.Bar(
            x=months,
            y=counts,
            name="Order Count",
            opacity=0.7,
            marker_color="#ff7f0e",
            hovertemplate='<b>%{x}</b><br>Orders: %{y}<extra></extra>'
        ),
        secondary_y=True,
    )

    # Update axes
    fig.update_yaxes(title_text="Revenue ($)", secondary_y=False)
    fig.update_yaxes(title_text="Number of Orders", secondary_y=True)
    fig.update_xaxes(title_text="Month")

    fig.update_layout(
        height=500,
        hovermode='x unified',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        )
    )

    st.plotly_chart(fig, use_container_width=True)

def create_top_products_chart(top_products_data):
    """Create top products chart"""
    if not top_products_data:
        st.warning("No top products data available")
        return

    # Process data
    names = []
    quantities = []
    order_counts = []

    for product_id, data in top_products_data[:10]:  # Top 10
        names.append(data["name"][:20] + "..." if len(data["name"]) > 20 else data["name"])
        quantities.append(data["total_quantity"])
        order_counts.append(data["order_count"])

    if not names:
        st.warning("No product data found")
        return

    # Create horizontal bar chart
    fig = px.bar(
        x=quantities,
        y=names,
        orientation='h',
        title="Top Products by Total Quantity Sold",
        labels={'x': 'Total Quantity', 'y': 'Product'},
        color=quantities,
        color_continuous_scale='blues'
    )

    fig.update_traces(
        hovertemplate='<b>%{y}</b><br>Quantity: %{x}<br>Orders: ' +
                     str([f'{c}' for c in order_counts]).replace("'", "") + '<extra></extra>'
    )

    fig.update_layout(
        height=400,
        showlegend=False,
        yaxis={'categoryorder': 'total ascending'}
    )

    st.plotly_chart(fig, use_container_width=True)

def create_customer_analysis_chart(customer_data):
    """Create customer analysis chart"""
    customers = customer_data.get("customer_details", [])

    if not customers:
        st.warning("No customer data available")
        return

    # Process data for scatter plot
    names = []
    orders = []
    spent = []

    for customer in customers:
        if customer["total_orders"] > 0:  # Only active customers
            names.append(customer["name"][:15] + "..." if len(customer["name"]) > 15 else customer["name"])
            orders.append(customer["total_orders"])
            spent.append(customer["total_spent"])

    if not names:
        st.warning("No active customer data found")
        return

    # Create scatter plot
    fig = px.scatter(
        x=orders,
        y=spent,
        hover_name=names,
        title="Customer Value Analysis",
        labels={'x': 'Number of Orders', 'y': 'Total Spent ($)'},
        size=[max(1, s/100) for s in spent],  # Size by amount spent
        color=orders,
        color_continuous_scale='viridis'
    )

    fig.update_traces(
        hovertemplate='<b>%{hovertext}</b><br>Orders: %{x}<br>Spent: $%{y:,.2f}<extra></extra>'
    )

    fig.update_layout(
        height=400,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

@st.cache_data(ttl=60)
def search_documents(_db_client, query, search_type):
    """Search documents based on query and type with caching"""
    if not _db_client or not query.strip():
        return [], "No query provided"

    try:
        # Define search selectors based on type
        if search_type == "Products":
            selector = {
                "type": "product",
                "$or": [
                    {"name": {"$regex": f"(?i).*{query}.*"}},
                    {"description": {"$regex": f"(?i).*{query}.*"}},
                    {"category": {"$regex": f"(?i).*{query}.*"}}
                ]
            }
        elif search_type == "Customers":
            selector = {
                "type": "customer",
                "$or": [
                    {"name": {"$regex": f"(?i).*{query}.*"}},
                    {"email": {"$regex": f"(?i).*{query}.*"}},
                    {"city": {"$regex": f"(?i).*{query}.*"}}
                ]
            }
        elif search_type == "Orders":
            selector = {
                "type": "order",
                "$or": [
                    {"status": {"$regex": f"(?i).*{query}.*"}},
                    {"customer_id": {"$regex": f"(?i).*{query}.*"}}
                ]
            }
        else:  # All
            selector = {
                "$or": [
                    {
                        "type": "product",
                        "$or": [
                            {"name": {"$regex": f"(?i).*{query}.*"}},
                            {"description": {"$regex": f"(?i).*{query}.*"}},
                            {"category": {"$regex": f"(?i).*{query}.*"}}
                        ]
                    },
                    {
                        "type": "customer",
                        "$or": [
                            {"name": {"$regex": f"(?i).*{query}.*"}},
                            {"email": {"$regex": f"(?i).*{query}.*"}},
                            {"city": {"$regex": f"(?i).*{query}.*"}}
                        ]
                    },
                    {
                        "type": "order",
                        "$or": [
                            {"status": {"$regex": f"(?i).*{query}.*"}}
                        ]
                    }
                ]
            }

        result = _db_client.find(selector, limit=10)
        if result["success"]:
            return result["documents"], None
        else:
            return [], result.get("error", "Search failed")

    except Exception as e:
        return [], str(e)

def display_search_results(db_client, query, search_type):
    """Display search results in sidebar"""
    if not db_client:
        st.sidebar.error("Database not connected")
        return

    with st.spinner("Searching..."):
        results, error = search_documents(db_client, query, search_type)

    if error:
        st.sidebar.error(f"Search error: {error}")
        return

    if not results:
        st.sidebar.info("No results found")
        return

    st.sidebar.markdown(f"**Found {len(results)} result(s):**")

    for i, doc in enumerate(results):
        doc_type = doc.get("type", "unknown").title()
        doc_id = doc.get("_id", "N/A")

        with st.sidebar.expander(f"{doc_type} - {doc_id[:12]}..."):
            if doc_type == "Product":
                st.write(f"**Name:** {doc.get('name', 'N/A')}")
                st.write(f"**Category:** {doc.get('category', 'N/A')}")
                st.write(f"**Price:** ${doc.get('price', 0):.2f}")
            elif doc_type == "Customer":
                st.write(f"**Name:** {doc.get('name', 'N/A')}")
                st.write(f"**Email:** {doc.get('email', 'N/A')}")
                st.write(f"**City:** {doc.get('city', 'N/A')}")
            elif doc_type == "Order":
                st.write(f"**Status:** {doc.get('status', 'N/A')}")
                st.write(f"**Total:** ${doc.get('total_amount', 0):.2f}")
                st.write(f"**Customer:** {doc.get('customer_id', 'N/A')[:12]}...")

            # Show full JSON option
            if st.button(f"Show JSON", key=f"json_{i}"):
                st.json(doc)

def main():
    """Main application function"""

    # Header
    st.markdown('<h1 class="main-header">📊 CouchDB Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Dashboard", "Data Explorer", "CRUD Operations", "Raw Data"])

    # Connection status
    st.sidebar.markdown("### Connection Status")

    with st.spinner("Connecting to CouchDB..."):
        db_client, analytics, error = get_database_connection()

    # Search bar (only if connected)
    if not error:
        st.sidebar.markdown("### 🔍 Quick Search")
        search_query = st.sidebar.text_input("Search documents...", placeholder="Enter search term")
        search_type = st.sidebar.selectbox("Search in:", ["All", "Products", "Customers", "Orders"])

        # Search results
        if search_query:
            display_search_results(db_client, search_query, search_type)

    if error:
        st.sidebar.markdown('<p class="error-message">❌ Connection Failed</p>', unsafe_allow_html=True)
        st.sidebar.error(f"Error: {error}")
        st.error("Cannot connect to CouchDB. Please check your configuration and ensure CouchDB is running.")
        st.info("Make sure to:")
        st.markdown("""
        - Start CouchDB service
        - Check .env file configuration
        - Run setup_couchdb.py first
        - Run scripts/etl.py to populate data
        """)
        return
    else:
        st.sidebar.markdown('<p class="success-message">✅ Connected</p>', unsafe_allow_html=True)

        # Database info
        db_info = db_client.get_database_info()
        if db_info["success"]:
            info = db_info["info"]
            st.sidebar.info(f"Database: {info.get('db_name', 'N/A')}")
            st.sidebar.info(f"Documents: {info.get('doc_count', 0)}")

    # Main content based on selected page
    if page == "Dashboard":
        display_dashboard(analytics)
    elif page == "Data Explorer":
        display_data_explorer(analytics)
    elif page == "CRUD Operations":
        display_crud_operations(db_client)
    elif page == "Raw Data":
        display_raw_data(db_client, analytics)

def display_dashboard(analytics):
    """Display main dashboard"""
    st.header("Key Performance Indicators")

    # Load data
    with st.spinner("Loading analytics data..."):
        sales_data, sales_error = load_sales_data(analytics)
        customer_data, customer_error = load_customer_data(analytics)
        product_data, product_error = load_product_data(analytics)
        top_products, top_products_error = load_top_products(analytics, 10)
        sales_by_month, sales_month_error = load_sales_by_month(analytics)

    # Check for errors
    if any([sales_error, customer_error, product_error]):
        st.error("Some data could not be loaded:")
        if sales_error:
            st.error(f"Sales: {sales_error}")
        if customer_error:
            st.error(f"Customers: {customer_error}")
        if product_error:
            st.error(f"Products: {product_error}")
        return

    # KPI Cards
    create_kpi_cards(sales_data, customer_data, product_data)

    st.markdown("---")

    # Charts Row 1
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Order Status Distribution")
        create_order_status_chart(sales_data)

    with col2:
        st.subheader("Products by Category")
        create_product_category_chart(product_data)

    # Charts Row 2
    st.subheader("Sales Trend Analysis")
    create_sales_trend_chart(sales_by_month)

    # Charts Row 3
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Top Products")
        create_top_products_chart(top_products)

    with col4:
        st.subheader("Customer Value Analysis")
        create_customer_analysis_chart(customer_data)

def display_data_explorer(analytics):
    """Display data exploration tools"""
    st.header("Data Explorer")

    # Query builder
    st.subheader("Custom Query Builder")

    doc_type = st.selectbox("Document Type", ["product", "customer", "order", "analytics_event"])

    # Dynamic filters based on document type
    filters = {}

    if doc_type == "product":
        category = st.text_input("Category (optional)")
        if category:
            filters["category"] = category

        col1, col2 = st.columns(2)
        with col1:
            min_price = st.number_input("Min Price", min_value=0.0, value=0.0)
        with col2:
            max_price = st.number_input("Max Price", min_value=0.0, value=1000.0)

        if min_price > 0 or max_price < 1000:
            filters["price"] = {"$gte": min_price, "$lte": max_price}

    elif doc_type == "order":
        status = st.selectbox("Status (optional)", ["", "pending", "confirmed", "shipped", "delivered", "cancelled"])
        if status:
            filters["status"] = status

    # Build query
    selector = {"type": doc_type}
    selector.update(filters)

    limit = st.slider("Limit results", 1, 100, 20)

    if st.button("Execute Query"):
        with st.spinner("Executing query..."):
            result = analytics.db.find(selector, limit=limit)

            if result["success"]:
                documents = result["documents"]
                st.success(f"Found {len(documents)} documents")

                if documents:
                    # Display as JSON
                    st.json(documents)

                    # Download button
                    json_str = json.dumps(documents, indent=2, default=str)
                    st.download_button(
                        label="Download as JSON",
                        data=json_str,
                        file_name=f"{doc_type}_query_results.json",
                        mime="application/json"
                    )
            else:
                st.error(f"Query failed: {result.get('error', 'Unknown error')}")

def display_raw_data(db_client, analytics):
    """Display raw data and database operations"""
    st.header("Raw Data & Operations")

    # Database statistics
    st.subheader("Database Statistics")
    db_info = db_client.get_database_info()
    if db_info["success"]:
        info = db_info["info"]
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Documents", info.get("doc_count", 0))
        with col2:
            st.metric("Deleted Documents", info.get("doc_del_count", 0))
        with col3:
            db_size_bytes = info.get('sizes', {}).get('active', 0)
            st.metric("Database Size", f"{db_size_bytes / 1024 / 1024:.2f} MB")

    # Sample documents
    st.subheader("Sample Documents by Type")

    doc_types = ["product", "customer", "order", "analytics_event"]

    for doc_type in doc_types:
        with st.expander(f"Sample {doc_type.title()} Documents"):
            result = analytics.db.find({"type": doc_type}, limit=3)
            if result["success"] and result["documents"]:
                for i, doc in enumerate(result["documents"]):
                    st.json({f"{doc_type}_{i+1}": doc})
            else:
                st.info(f"No {doc_type} documents found")

def display_crud_operations(db_client):
    """Display CRUD operations interface"""
    if not db_client:
        st.error("Database connection required for CRUD operations")
        return

    st.header("🛠️ CRUD Operations")
    st.markdown("Create, Read, Update, and Delete documents in the CouchDB database")

    # CRUD operation selector
    operation = st.selectbox("Select Operation", ["Create", "Read", "Update", "Delete"])

    if operation == "Create":
        display_create_interface(db_client)
    elif operation == "Read":
        display_read_interface(db_client)
    elif operation == "Update":
        display_update_interface(db_client)
    elif operation == "Delete":
        display_delete_interface(db_client)

def display_create_interface(db_client):
    """Display interface for creating documents"""
    st.subheader("📝 Create New Document")

    doc_type = st.selectbox("Document Type", ["Product", "Customer", "Order"])

    if doc_type == "Product":
        with st.form("create_product_form"):
            st.markdown("### Product Information")
            name = st.text_input("Product Name *", placeholder="e.g., Smartphone XY Pro")
            category = st.selectbox("Category", ["Electronics", "Home & Kitchen", "Sports & Fitness", "Books", "Clothing", "Other"])
            price = st.number_input("Price ($)", min_value=0.01, value=1.0, step=0.01)
            description = st.text_area("Description", placeholder="Product description...")
            status = st.selectbox("Status", ["active", "inactive", "discontinued"])

            # Metadata
            st.markdown("### Additional Information (Optional)")
            brand = st.text_input("Brand")
            warranty = st.text_input("Warranty")
            color = st.text_input("Color")

            submitted = st.form_submit_button("Create Product")

            if submitted:
                if not name:
                    st.error("Product name is required")
                else:
                    metadata = {}
                    if brand: metadata["brand"] = brand
                    if warranty: metadata["warranty"] = warranty
                    if color: metadata["color"] = color

                    product_doc = ProductSchema.create_product(
                        name=name,
                        category=category,
                        price=price,
                        description=description,
                        status=status,
                        metadata=metadata
                    )

                    result = db_client.create_document(product_doc)
                    if result["success"]:
                        st.success(f"Product created successfully! ID: {product_doc['_id']}")
                        st.json(product_doc)
                    else:
                        st.error(f"Failed to create product: {result.get('error', 'Unknown error')}")

    elif doc_type == "Customer":
        with st.form("create_customer_form"):
            st.markdown("### Customer Information")
            name = st.text_input("Customer Name *", placeholder="e.g., John Doe")
            email = st.text_input("Email *", placeholder="john.doe@email.com")
            phone = st.text_input("Phone", placeholder="+1-555-0123")

            # Address
            st.markdown("### Address (Optional)")
            street = st.text_input("Street")
            city = st.text_input("City")
            zip_code = st.text_input("ZIP Code")
            country = st.text_input("Country")

            submitted = st.form_submit_button("Create Customer")

            if submitted:
                if not name or not email:
                    st.error("Name and email are required")
                else:
                    address = {}
                    if street: address["street"] = street
                    if city: address["city"] = city
                    if zip_code: address["zip"] = zip_code
                    if country: address["country"] = country

                    customer_doc = CustomerSchema.create_customer(
                        name=name,
                        email=email,
                        phone=phone,
                        address=address if address else None
                    )

                    result = db_client.create_document(customer_doc)
                    if result["success"]:
                        st.success(f"Customer created successfully! ID: {customer_doc['_id']}")
                        st.json(customer_doc)
                    else:
                        st.error(f"Failed to create customer: {result.get('error', 'Unknown error')}")

    elif doc_type == "Order":
        with st.form("create_order_form"):
            st.markdown("### Order Information")

            # Get customers for dropdown
            customers_result = db_client.find({"type": "customer"}, limit=50)
            if customers_result["success"] and customers_result["documents"]:
                customer_options = {f"{c['name']} ({c['email']})": c["_id"]
                                 for c in customers_result["documents"]}
                selected_customer = st.selectbox("Customer *", list(customer_options.keys()))
                customer_id = customer_options[selected_customer] if selected_customer else ""
            else:
                customer_id = st.text_input("Customer ID *", placeholder="customer_...")
                st.warning("No customers found in database. Please enter customer ID manually.")

            status = st.selectbox("Status", ["pending", "confirmed", "shipped", "delivered", "cancelled"])

            # Products - simplified for demo
            st.markdown("### Products")
            st.info("Simplified product entry - in a real application, you'd have a dynamic product selector")
            product_id = st.text_input("Product ID", placeholder="product_...")
            quantity = st.number_input("Quantity", min_value=1, value=1)
            unit_price = st.number_input("Unit Price ($)", min_value=0.01, value=1.0)

            total = quantity * unit_price
            st.metric("Total Amount", f"${total:.2f}")

            submitted = st.form_submit_button("Create Order")

            if submitted:
                if not customer_id:
                    st.error("Customer ID is required")
                elif not product_id:
                    st.error("Product ID is required")
                else:
                    products = [{"product_id": product_id, "quantity": quantity, "price": unit_price}]

                    order_doc = OrderSchema.create_order(
                        customer_id=customer_id,
                        products=products,
                        total=total,
                        status=status
                    )

                    result = db_client.create_document(order_doc)
                    if result["success"]:
                        st.success(f"Order created successfully! ID: {order_doc['_id']}")
                        st.json(order_doc)
                    else:
                        st.error(f"Failed to create order: {result.get('error', 'Unknown error')}")

def display_read_interface(db_client):
    """Display interface for reading documents"""
    st.subheader("📖 Read Documents")

    read_method = st.radio("Read Method", ["By ID", "Query by Type", "Advanced Search"])

    if read_method == "By ID":
        doc_id = st.text_input("Document ID", placeholder="e.g., product_12345...")

        if st.button("Get Document") and doc_id:
            result = db_client.read_document(doc_id)
            if result["success"]:
                st.success("Document found!")
                st.json(result["document"])
            else:
                st.error(f"Document not found: {result.get('error', 'Unknown error')}")

    elif read_method == "Query by Type":
        doc_type = st.selectbox("Document Type", ["product", "customer", "order", "analytics_event"])
        limit = st.slider("Number of results", 1, 50, 10)

        if st.button("Query Documents"):
            result = db_client.find({"type": doc_type}, limit=limit)
            if result["success"]:
                documents = result["documents"]
                st.success(f"Found {len(documents)} {doc_type} documents")

                for i, doc in enumerate(documents):
                    with st.expander(f"{doc_type.title()} {i+1}: {doc.get('_id', 'No ID')[:20]}..."):
                        st.json(doc)
            else:
                st.error(f"Query failed: {result.get('error', 'Unknown error')}")

    elif read_method == "Advanced Search":
        st.markdown("### Custom Query Builder")

        query_json = st.text_area(
            "CouchDB Mango Query (JSON)",
            value='{"type": "product", "price": {"$gt": 50}}',
            height=100,
            help="Enter a valid CouchDB Mango query"
        )
        limit = st.slider("Limit results", 1, 100, 20)

        if st.button("Execute Query"):
            try:
                query = json.loads(query_json)
                result = db_client.find(query, limit=limit)

                if result["success"]:
                    documents = result["documents"]
                    st.success(f"Query executed successfully! Found {len(documents)} documents")

                    if documents:
                        for i, doc in enumerate(documents):
                            with st.expander(f"Document {i+1}: {doc.get('_id', 'No ID')[:20]}..."):
                                st.json(doc)
                    else:
                        st.info("No documents matched the query")
                else:
                    st.error(f"Query failed: {result.get('error', 'Unknown error')}")
            except json.JSONDecodeError:
                st.error("Invalid JSON query format")

def display_update_interface(db_client):
    """Display interface for updating documents"""
    st.subheader("✏️ Update Documents")

    # Step 1: Get document
    st.markdown("### Step 1: Find Document to Update")
    doc_id = st.text_input("Document ID", placeholder="e.g., product_12345...")

    if doc_id and st.button("Load Document"):
        st.session_state.update_doc_id = doc_id
        result = db_client.read_document(doc_id)
        if result["success"]:
            st.session_state.update_document = result["document"]
            st.success("Document loaded successfully!")
        else:
            st.error(f"Document not found: {result.get('error', 'Unknown error')}")
            if "update_document" in st.session_state:
                del st.session_state.update_document

    # Step 2: Update document
    if hasattr(st.session_state, 'update_document'):
        st.markdown("### Step 2: Update Document Fields")
        doc = st.session_state.update_document
        doc_type = doc.get("type", "unknown")

        st.info(f"Updating {doc_type} document: {doc.get('_id', 'No ID')}")

        if doc_type == "product":
            with st.form("update_product_form"):
                name = st.text_input("Product Name", value=doc.get("name", ""))
                category = st.text_input("Category", value=doc.get("category", ""))
                price = st.number_input("Price ($)", value=doc.get("price", 0.0), min_value=0.01)
                description = st.text_area("Description", value=doc.get("description", ""))
                status = st.selectbox("Status", ["active", "inactive", "discontinued"],
                                    index=["active", "inactive", "discontinued"].index(doc.get("status", "active")))

                submitted = st.form_submit_button("Update Product")

                if submitted:
                    updated_doc = doc.copy()
                    updated_doc.update({
                        "name": name,
                        "category": category,
                        "price": price,
                        "description": description,
                        "status": status,
                        "updated_at": datetime.now().isoformat()
                    })

                    result = db_client.update_document(updated_doc)
                    if result["success"]:
                        st.success("Product updated successfully!")
                        st.json(updated_doc)
                        del st.session_state.update_document
                    else:
                        st.error(f"Update failed: {result.get('error', 'Unknown error')}")

        elif doc_type == "customer":
            with st.form("update_customer_form"):
                name = st.text_input("Customer Name", value=doc.get("name", ""))
                email = st.text_input("Email", value=doc.get("email", ""))
                phone = st.text_input("Phone", value=doc.get("phone", ""))

                address = doc.get("address", {})
                street = st.text_input("Street", value=address.get("street", ""))
                city = st.text_input("City", value=address.get("city", ""))

                submitted = st.form_submit_button("Update Customer")

                if submitted:
                    updated_doc = doc.copy()
                    updated_doc.update({
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "address": {"street": street, "city": city},
                        "updated_at": datetime.now().isoformat()
                    })

                    result = db_client.update_document(updated_doc)
                    if result["success"]:
                        st.success("Customer updated successfully!")
                        st.json(updated_doc)
                        del st.session_state.update_document
                    else:
                        st.error(f"Update failed: {result.get('error', 'Unknown error')}")

        elif doc_type == "order":
            with st.form("update_order_form"):
                status = st.selectbox("Status", ["pending", "confirmed", "shipped", "delivered", "cancelled"],
                                    index=["pending", "confirmed", "shipped", "delivered", "cancelled"].index(doc.get("status", "pending")))
                total = st.number_input("Total Amount", value=doc.get("total", 0.0), min_value=0.01)

                submitted = st.form_submit_button("Update Order")

                if submitted:
                    updated_doc = doc.copy()
                    updated_doc.update({
                        "status": status,
                        "total": total,
                        "updated_at": datetime.now().isoformat()
                    })

                    result = db_client.update_document(updated_doc)
                    if result["success"]:
                        st.success("Order updated successfully!")
                        st.json(updated_doc)
                        del st.session_state.update_document
                    else:
                        st.error(f"Update failed: {result.get('error', 'Unknown error')}")

        else:
            st.warning(f"Update interface not implemented for document type: {doc_type}")
            st.json(doc)

def display_delete_interface(db_client):
    """Display interface for deleting documents"""
    st.subheader("🗑️ Delete Documents")
    st.warning("⚠️ This action cannot be undone. Please be careful!")

    delete_method = st.radio("Delete Method", ["Single Document", "Bulk Delete by Query"])

    if delete_method == "Single Document":
        doc_id = st.text_input("Document ID to Delete", placeholder="e.g., product_12345...")

        # Preview document before deletion
        if doc_id and st.button("Preview Document"):
            result = db_client.read_document(doc_id)
            if result["success"]:
                st.json(result["document"])
                st.session_state.delete_preview = result["document"]
            else:
                st.error(f"Document not found: {result.get('error', 'Unknown error')}")

        # Confirm deletion
        if hasattr(st.session_state, 'delete_preview'):
            st.error("⚠️ You are about to delete this document:")
            confirm = st.checkbox("I confirm I want to delete this document")

            if confirm and st.button("🗑️ Delete Document", type="primary"):
                result = db_client.delete_document(st.session_state.delete_preview)
                if result["success"]:
                    st.success("Document deleted successfully!")
                    del st.session_state.delete_preview
                else:
                    st.error(f"Delete failed: {result.get('error', 'Unknown error')}")

    elif delete_method == "Bulk Delete by Query":
        st.markdown("### Bulk Delete by Document Type")
        doc_type = st.selectbox("Document Type to Delete", ["product", "customer", "order", "analytics_event"])

        # Additional filters
        with st.expander("Additional Filters (Optional)"):
            if doc_type == "product":
                status_filter = st.selectbox("Status Filter", ["All", "active", "inactive", "discontinued"])
                category_filter = st.text_input("Category Filter (optional)")
            elif doc_type == "order":
                status_filter = st.selectbox("Status Filter", ["All", "pending", "confirmed", "shipped", "delivered", "cancelled"])

        # Preview what will be deleted
        if st.button("Preview Documents to Delete"):
            query = {"type": doc_type}

            if doc_type == "product":
                if status_filter != "All":
                    query["status"] = status_filter
                if category_filter:
                    query["category"] = category_filter
            elif doc_type == "order":
                if status_filter != "All":
                    query["status"] = status_filter

            result = db_client.find(query, limit=50)
            if result["success"]:
                documents = result["documents"]
                st.info(f"Found {len(documents)} documents that would be deleted:")

                for doc in documents[:5]:  # Show first 5
                    st.json(doc)

                if len(documents) > 5:
                    st.info(f"... and {len(documents) - 5} more documents")

                st.session_state.bulk_delete_docs = documents
                st.session_state.bulk_delete_query = query
            else:
                st.error(f"Query failed: {result.get('error', 'Unknown error')}")

        # Confirm bulk deletion
        if hasattr(st.session_state, 'bulk_delete_docs'):
            docs_count = len(st.session_state.bulk_delete_docs)
            st.error(f"⚠️ You are about to delete {docs_count} documents!")

            confirm_text = st.text_input(f"Type 'DELETE {docs_count} DOCUMENTS' to confirm:")

            if confirm_text == f"DELETE {docs_count} DOCUMENTS" and st.button("🗑️ BULK DELETE", type="primary"):
                success_count = 0
                error_count = 0

                for doc in st.session_state.bulk_delete_docs:
                    result = db_client.delete_document(doc)
                    if result["success"]:
                        success_count += 1
                    else:
                        error_count += 1

                if error_count == 0:
                    st.success(f"Successfully deleted {success_count} documents!")
                else:
                    st.warning(f"Deleted {success_count} documents, {error_count} failed")

                del st.session_state.bulk_delete_docs
                del st.session_state.bulk_delete_query

if __name__ == "__main__":
    main()