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

def main():
    """Main application function"""

    # Header
    st.markdown('<h1 class="main-header">📊 CouchDB Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")

    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", ["Dashboard", "Data Explorer", "Raw Data"])

    # Connection status
    st.sidebar.markdown("### Connection Status")

    with st.spinner("Connecting to CouchDB..."):
        db_client, analytics, error = get_database_connection()

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

if __name__ == "__main__":
    main()