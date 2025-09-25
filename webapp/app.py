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
            label="Total Commandes",
            value=sales_data.get("total_orders", 0),
            delta=f"+{sales_data.get('total_orders', 0) - 20}"  # Mock delta
        )

    with col2:
        st.metric(
            label="Chiffre d'Affaires Total",
            value=f"{sales_data.get('total_revenue', 0):,.2f} €",
            delta=f"+{sales_data.get('total_revenue', 0) * 0.1:.2f}"  # Mock 10% increase
        )

    with col3:
        st.metric(
            label="Valeur Moyenne Commande",
            value=f"{sales_data.get('average_order_value', 0):.2f} €",
            delta=f"+{sales_data.get('average_order_value', 0) * 0.05:.2f}"  # Mock 5% increase
        )

    with col4:
        st.metric(
            label="Total Clients",
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

@st.cache_data(ttl=300)
def get_product_categories(_db_client):
    """Get all distinct product categories from database"""
    if not _db_client:
        return []

    try:
        # Get all products to extract categories
        result = _db_client.find({"type": "product"}, limit=1000)
        if result["success"]:
            categories = set()
            for product in result["documents"]:
                category = product.get("category", "").strip()
                if category:
                    categories.add(category)
            return sorted(list(categories))
        else:
            return []
    except Exception as e:
        return []

@st.cache_data(ttl=300)
def get_available_products(_db_client):
    """Get all available products for order creation"""
    if not _db_client:
        return {}

    try:
        # Get all active products
        result = _db_client.find({"type": "product", "status": "active"}, limit=1000)
        if result["success"]:
            products = {}
            for product in result["documents"]:
                product_id = product.get("_id", "")
                name = product.get("name", "Produit sans nom")
                price = product.get("price", 0.0)
                category = product.get("category", "N/A")

                # Create a user-friendly display name
                display_name = f"{name} - {category} ({price:.2f} €)"
                products[display_name] = {
                    "id": product_id,
                    "name": name,
                    "price": price,
                    "category": category
                }
            return products
        else:
            return {}
    except Exception as e:
        return {}

@st.cache_data(ttl=300)
def get_all_products(_db_client):
    """Get all products for update interface"""
    if not _db_client:
        return {}

    try:
        result = _db_client.find({"type": "product"}, limit=1000)
        if result["success"]:
            products = {}
            for product in result["documents"]:
                product_id = product.get("_id", "")
                name = product.get("name", "Produit sans nom")
                price = product.get("price", 0.0)
                category = product.get("category", "N/A")
                status = product.get("status", "active")

                # Create a user-friendly display name
                display_name = f"{name} - {category} ({price:.2f} €) [{status}]"
                products[display_name] = {
                    "id": product_id,
                    "document": product
                }
            return products
        else:
            return {}
    except Exception as e:
        return {}

@st.cache_data(ttl=300)
def get_all_customers(_db_client):
    """Get all customers for update interface"""
    if not _db_client:
        return {}

    try:
        result = _db_client.find({"type": "customer"}, limit=1000)
        if result["success"]:
            customers = {}
            for customer in result["documents"]:
                customer_id = customer.get("_id", "")
                name = customer.get("name", "Client sans nom")
                email = customer.get("email", "N/A")

                # Create a user-friendly display name
                display_name = f"{name} ({email})"
                customers[display_name] = {
                    "id": customer_id,
                    "document": customer
                }
            return customers
        else:
            return {}
    except Exception as e:
        return {}

@st.cache_data(ttl=300)
def get_all_orders(_db_client):
    """Get all orders for update interface"""
    if not _db_client:
        return {}

    try:
        result = _db_client.find({"type": "order"}, limit=1000)
        if result["success"]:
            orders = {}
            for order in result["documents"]:
                order_id = order.get("_id", "")
                customer_id = order.get("customer_id", "N/A")
                total = order.get("total", 0.0)
                status = order.get("status", "pending")
                created_at = order.get("created_at", "")[:10]  # Date only

                # Create a user-friendly display name
                display_name = f"Commande {total:.2f} € - {status} ({created_at})"
                orders[display_name] = {
                    "id": order_id,
                    "document": order
                }
            return orders
        else:
            return {}
    except Exception as e:
        return {}

@st.cache_data(ttl=60)
def search_documents(_db_client, query, search_type):
    """Search documents based on query and type with caching"""
    if not _db_client or not query.strip():
        return [], "No query provided"

    try:
        # Define search selectors based on type
        if search_type == "Produits":
            selector = {
                "type": "product",
                "$or": [
                    {"name": {"$regex": f"(?i).*{query}.*"}},
                    {"description": {"$regex": f"(?i).*{query}.*"}},
                    {"category": {"$regex": f"(?i).*{query}.*"}}
                ]
            }
        elif search_type == "Clients":
            selector = {
                "type": "customer",
                "$or": [
                    {"name": {"$regex": f"(?i).*{query}.*"}},
                    {"email": {"$regex": f"(?i).*{query}.*"}},
                    {"city": {"$regex": f"(?i).*{query}.*"}}
                ]
            }
        elif search_type == "Commandes":
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
        st.sidebar.error("Base de données non connectée")
        return

    with st.spinner("Recherche en cours..."):
        results, error = search_documents(db_client, query, search_type)

    if error:
        st.sidebar.error(f"Erreur de recherche : {error}")
        return

    if not results:
        st.sidebar.info("Aucun résultat trouvé")
        return

    st.sidebar.markdown(f"**Trouvé {len(results)} résultat(s) :**")

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
    page = st.sidebar.selectbox("Choisir une page", ["Tableau de Bord", "Explorateur de Données", "Opérations CRUD", "Données Brutes"])

    # Connection status
    st.sidebar.markdown("### État de la Connexion")

    with st.spinner("Connexion à CouchDB..."):
        db_client, analytics, error = get_database_connection()

    # Search bar (only if connected)
    if not error:
        st.sidebar.markdown("### 🔍 Recherche Rapide")
        search_query = st.sidebar.text_input("Rechercher des documents...", placeholder="Saisir un terme de recherche")
        search_type = st.sidebar.selectbox("Rechercher dans :", ["Tout", "Produits", "Clients", "Commandes"])

        # Search results
        if search_query:
            display_search_results(db_client, search_query, search_type)

    if error:
        st.sidebar.markdown('<p class="error-message">❌ Connexion Échouée</p>', unsafe_allow_html=True)
        st.sidebar.error(f"Erreur : {error}")
        st.error("Impossible de se connecter à CouchDB. Veuillez vérifier votre configuration et vous assurer que CouchDB fonctionne.")
        st.info("Assurez-vous de :")
        st.markdown("""
        - Démarrer le service CouchDB
        - Vérifier la configuration du fichier .env
        - Exécuter setup_couchdb.py en premier
        - Exécuter scripts/etl.py pour peupler les données
        """)
        return
    else:
        st.sidebar.markdown('<p class="success-message">✅ Connecté</p>', unsafe_allow_html=True)

        # Database info
        db_info = db_client.get_database_info()
        if db_info["success"]:
            info = db_info["info"]
            st.sidebar.info(f"Database: {info.get('db_name', 'N/A')}")
            st.sidebar.info(f"Documents: {info.get('doc_count', 0)}")

    # Main content based on selected page
    if page == "Tableau de Bord":
        display_dashboard(analytics)
    elif page == "Explorateur de Données":
        display_data_explorer(analytics)
    elif page == "Opérations CRUD":
        display_crud_operations(db_client)
    elif page == "Données Brutes":
        display_raw_data(db_client, analytics)

def display_dashboard(analytics):
    """Display main dashboard"""
    st.header("Indicateurs Clés de Performance")

    if not analytics:
        st.error("Moteur d'analytique non disponible")
        return

    # Load data
    with st.spinner("Chargement des données analytiques..."):
        sales_data, sales_error = load_sales_data(analytics)
        customer_data, customer_error = load_customer_data(analytics)
        product_data, product_error = load_product_data(analytics)
        top_products, top_products_error = load_top_products(analytics, 10)
        sales_by_month, sales_month_error = load_sales_by_month(analytics)

    # Check for errors
    if any([sales_error, customer_error, product_error]):
        st.error("Certaines données n'ont pas pu être chargées :")
        if sales_error:
            st.error(f"Ventes : {sales_error}")
        if customer_error:
            st.error(f"Clients : {customer_error}")
        if product_error:
            st.error(f"Produits : {product_error}")
        return

    # KPI Cards
    create_kpi_cards(sales_data, customer_data, product_data)

    st.markdown("---")

    # Charts Row 1
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribution des Statuts de Commandes")
        create_order_status_chart(sales_data)

    with col2:
        st.subheader("Produits par Catégorie")
        create_product_category_chart(product_data)

    # Charts Row 2
    st.subheader("Analyse des Tendances de Vente")
    create_sales_trend_chart(sales_by_month)

    # Charts Row 3
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Meilleurs Produits")
        create_top_products_chart(top_products)

    with col4:
        st.subheader("Analyse de la Valeur Client")
        create_customer_analysis_chart(customer_data)

def display_data_explorer(analytics):
    """Display data exploration tools"""
    st.header("🔍 Explorateur de Données")

    # Query builder
    st.subheader("Générateur de Requêtes Personnalisées")

    doc_type = st.selectbox("Type de Document", ["product", "customer", "order", "analytics_event"],
                           format_func=lambda x: {"product": "Produit", "customer": "Client", "order": "Commande", "analytics_event": "Événement Analytics"}[x])

    # Dynamic filters based on document type
    filters = {}

    if doc_type == "product":
        # Get available categories from database
        available_categories = get_product_categories(analytics.db)
        if available_categories:
            category_options = ["Toutes"] + available_categories
            selected_category = st.selectbox("Catégorie", category_options)
            if selected_category != "Toutes":
                filters["category"] = selected_category
        else:
            st.info("Aucune catégorie trouvée dans la base de données")

        col1, col2 = st.columns(2)
        with col1:
            min_price = st.number_input("Prix Minimum", min_value=0.0, value=0.0)
        with col2:
            max_price = st.number_input("Prix Maximum", min_value=0.0, value=1000.0)

        if min_price > 0 or max_price < 1000:
            filters["price"] = {"$gte": min_price, "$lte": max_price}

    elif doc_type == "order":
        status = st.selectbox("Statut (optionnel)", ["", "pending", "confirmed", "shipped", "delivered", "cancelled"],
                             format_func=lambda x: {"": "Tous", "pending": "En attente", "confirmed": "Confirmé",
                                                   "shipped": "Expédié", "delivered": "Livré", "cancelled": "Annulé"}[x] if x else "Tous")
        if status:
            filters["status"] = status

    # Build query
    selector = {"type": doc_type}
    selector.update(filters)

    limit = st.slider("Limite des résultats", 1, 100, 20)

    if st.button("Exécuter la Requête"):
        with st.spinner("Exécution de la requête..."):
            result = analytics.db.find(selector, limit=limit)

            if result["success"]:
                documents = result["documents"]
                st.success(f"Trouvé {len(documents)} documents")

                if documents:
                    # Display as beautiful cards instead of JSON
                    display_documents_as_cards(documents, doc_type)

                    # Download button
                    json_str = json.dumps(documents, indent=2, default=str)
                    st.download_button(
                        label="Télécharger en JSON",
                        data=json_str,
                        file_name=f"{doc_type}_query_results.json",
                        mime="application/json"
                    )
            else:
                st.error(f"Échec de la requête : {result.get('error', 'Erreur inconnue')}")

def display_documents_as_cards(documents, doc_type):
    """Display documents as beautiful cards instead of JSON"""

    # Add custom CSS for dark theme cards
    st.markdown("""
    <style>
    .doc-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
        border: 1px solid #404040;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid #00d4aa;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .doc-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,212,170,0.2);
    }
    .doc-card-header {
        color: #00d4aa;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 1rem;
        text-shadow: 0 0 10px rgba(0,212,170,0.3);
    }
    .doc-field {
        margin: 0.7rem 0;
        padding: 0.3rem 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    .doc-field:last-child {
        border-bottom: none;
    }
    .doc-field-label {
        font-weight: bold;
        color: #b0b0b0;
        display: inline-block;
        width: 140px;
        font-size: 0.9rem;
    }
    .doc-field-value {
        color: #ffffff;
        background: rgba(255,255,255,0.05);
        padding: 0.3rem 0.7rem;
        border-radius: 6px;
        display: inline-block;
        border: 1px solid rgba(255,255,255,0.1);
        font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
    }
    .price-badge {
        background: linear-gradient(135deg, #00d4aa 0%, #00a085 100%);
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(0,212,170,0.3);
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
    }
    .status-badge {
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-weight: bold;
        color: white;
        text-shadow: 0 1px 2px rgba(0,0,0,0.3);
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .status-pending {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
    }
    .status-confirmed {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
    }
    .status-shipped {
        background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
    }
    .status-delivered {
        background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
    }
    .status-cancelled {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
    }
    .status-active {
        background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
    }
    .status-inactive {
        background: linear-gradient(135deg, #95a5a6 0%, #7f8c8d 100%);
    }

    /* Dark theme scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #2d2d2d;
    }
    ::-webkit-scrollbar-thumb {
        background: #00d4aa;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #00a085;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display cards in columns
    cols_per_row = 2 if doc_type == "product" else 3

    for i in range(0, len(documents), cols_per_row):
        cols = st.columns(cols_per_row)

        for j in range(cols_per_row):
            if i + j < len(documents):
                doc = documents[i + j]

                with cols[j]:
                    if doc_type == "product":
                        display_product_card(doc)
                    elif doc_type == "customer":
                        display_customer_card(doc)
                    elif doc_type == "order":
                        display_order_card(doc)
                    else:
                        display_generic_card(doc)

def display_product_card(doc):
    """Display a product as a card"""
    product_name = doc.get("name", "Produit sans nom")
    category = doc.get("category", "N/A")
    price = doc.get("price", 0)
    status = doc.get("status", "unknown")
    description = doc.get("description", "")
    doc_id = doc.get("_id", "")

    status_class = f"status-{status}"

    card_html = f"""
    <div class="doc-card">
        <div class="doc-card-header">🏷️ {product_name}</div>
        <div class="doc-field">
            <span class="doc-field-label">Catégorie:</span>
            <span class="doc-field-value">{category}</span>
        </div>
        <div class="doc-field">
            <span class="doc-field-label">Prix:</span>
            <span class="price-badge">{price:.2f} €</span>
        </div>
        <div class="doc-field">
            <span class="doc-field-label">Statut:</span>
            <span class="status-badge {status_class}">{status.title()}</span>
        </div>
        <div class="doc-field">
            <span class="doc-field-label">Description:</span>
            <span class="doc-field-value">{description[:100]}{'...' if len(description) > 100 else ''}</span>
        </div>
        <div class="doc-field">
            <span class="doc-field-label">ID:</span>
            <span class="doc-field-value">{doc_id[:20]}...</span>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # JSON option in expander
    with st.expander(f"Voir JSON - {product_name}"):
        st.json(doc)

def display_customer_card(doc):
    """Display a customer as a card"""
    name = doc.get("name", "Client sans nom")
    email = doc.get("email", "N/A")
    phone = doc.get("phone", "N/A")
    address = doc.get("address", {})
    city = address.get("city", "N/A") if address else "N/A"
    doc_id = doc.get("_id", "")

    card_html = f"""
    <div class="doc-card">
        <div class="doc-card-header">👤 {name}</div>
        <div class="doc-field">
            <span class="doc-field-label">Email:</span>
            <span class="doc-field-value">{email}</span>
        </div>
        <div class="doc-field">
            <span class="doc-field-label">Téléphone:</span>
            <span class="doc-field-value">{phone}</span>
        </div>
        <div class="doc-field">
            <span class="doc-field-label">Ville:</span>
            <span class="doc-field-value">{city}</span>
        </div>
        <div class="doc-field">
            <span class="doc-field-label">ID:</span>
            <span class="doc-field-value">{doc_id[:20]}...</span>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # JSON option in expander
    with st.expander(f"Voir JSON - {name}"):
        st.json(doc)

def display_order_card(doc):
    """Display an order as a card"""
    customer_id = doc.get("customer_id", "N/A")
    status = doc.get("status", "unknown")
    total = doc.get("total", 0)
    products = doc.get("products", [])
    doc_id = doc.get("_id", "")
    created_at = doc.get("created_at", "")

    # Format date
    try:
        from datetime import datetime
        if created_at:
            date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime("%d/%m/%Y %H:%M")
        else:
            formatted_date = "N/A"
    except:
        formatted_date = "N/A"

    status_class = f"status-{status}"

    card_html = f"""
    <div class="doc-card">
        <div class="doc-card-header">🛒 Commande</div>
        <div class="doc-field">
            <span class="doc-field-label">Client ID:</span>
            <span class="doc-field-value">{customer_id[:15]}...</span>
        </div>
        <div class="doc-field">
            <span class="doc-field-label">Statut:</span>
            <span class="status-badge {status_class}">{status.title()}</span>
        </div>
        <div class="doc-field">
            <span class="doc-field-label">Total:</span>
            <span class="price-badge">{total:.2f} €</span>
        </div>
        <div class="doc-field">
            <span class="doc-field-label">Produits:</span>
            <span class="doc-field-value">{len(products)} article(s)</span>
        </div>
        <div class="doc-field">
            <span class="doc-field-label">Date:</span>
            <span class="doc-field-value">{formatted_date}</span>
        </div>
        <div class="doc-field">
            <span class="doc-field-label">ID:</span>
            <span class="doc-field-value">{doc_id[:20]}...</span>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # JSON option in expander
    with st.expander(f"Voir JSON - Commande"):
        st.json(doc)

def display_generic_card(doc):
    """Display a generic document as a card"""
    doc_type = doc.get("type", "Document")
    doc_id = doc.get("_id", "")

    card_html = f"""
    <div class="doc-card">
        <div class="doc-card-header">📄 {doc_type.title()}</div>
        <div class="doc-field">
            <span class="doc-field-label">ID:</span>
            <span class="doc-field-value">{doc_id[:30]}...</span>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # JSON option in expander
    with st.expander(f"Voir JSON - {doc_type}"):
        st.json(doc)

def display_raw_data(db_client, analytics):
    """Display raw data and database operations"""
    st.header("📋 Données Brutes & Opérations")

    # Database statistics
    st.subheader("Statistiques de la Base de Données")
    db_info = db_client.get_database_info()
    if db_info["success"]:
        info = db_info["info"]
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Documents", info.get("doc_count", 0))
        with col2:
            st.metric("Documents Supprimés", info.get("doc_del_count", 0))
        with col3:
            db_size_bytes = info.get('sizes', {}).get('active', 0)
            st.metric("Taille Base de Données", f"{db_size_bytes / 1024 / 1024:.2f} MB")

    # Sample documents
    st.subheader("Échantillons de Documents par Type")

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

                    result = db_client.create(product_doc)
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

                    result = db_client.create(customer_doc)
                    if result["success"]:
                        st.success(f"Customer created successfully! ID: {customer_doc['_id']}")
                        st.json(customer_doc)
                    else:
                        st.error(f"Failed to create customer: {result.get('error', 'Unknown error')}")

    elif doc_type == "Order":
        st.markdown("### 📋 Création de Commande")

        # Part 1: Dynamic product selection (outside form for real-time updates)
        st.markdown("#### 🔍 Sélection Dynamique")

        # Get customers for dropdown
        customers_result = db_client.find({"type": "customer"}, limit=50)
        if customers_result["success"] and customers_result["documents"]:
            customer_options = {f"{c['name']} ({c['email']})": c["_id"]
                             for c in customers_result["documents"]}
            selected_customer = st.selectbox("Client *", list(customer_options.keys()))
            customer_id = customer_options[selected_customer] if selected_customer else ""
        else:
            customer_id = st.text_input("ID Client *", placeholder="customer_...")
            st.warning("Aucun client trouvé dans la base de données.")

        # Get available products
        available_products = get_available_products(db_client)

        if available_products:
            selected_product_display = st.selectbox(
                "Sélectionner un produit *",
                list(available_products.keys()),
                key="product_selector"
            )

            if selected_product_display:
                product_info = available_products[selected_product_display]
                product_id = product_info["id"]
                suggested_price = product_info["price"]

                # Display product info with enhanced styling
                st.markdown("#### 📦 Informations du Produit")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                padding: 15px; border-radius: 10px; color: white; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: white;">📝 {product_info['name']}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                                padding: 15px; border-radius: 10px; color: white; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: white;">🏷️ {product_info['category']}</h4>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                                padding: 15px; border-radius: 10px; color: white; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: white;">💰 {suggested_price:.2f} €</h4>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("#### ⚙️ Configuration de la Commande")

                # Dynamic inputs (outside form)
                col_qty, col_price = st.columns(2)

                with col_qty:
                    quantity = st.number_input(
                        "Quantité",
                        min_value=1,
                        value=1,
                        key="quantity_input",
                        help="Modifiez la quantité pour voir le total se mettre à jour"
                    )

                with col_price:
                    unit_price = st.number_input(
                        "Prix unitaire (€)",
                        min_value=0.01,
                        value=suggested_price,
                        step=0.01,
                        key="price_input",
                        help="Prix par unité (pré-rempli avec le prix du produit)"
                    )

                # Dynamic total calculation
                total = quantity * unit_price

                # Visual total display
                st.markdown("#### 💵 Résumé de la Commande")
                col_summary1, col_summary2, col_summary3 = st.columns(3)

                with col_summary1:
                    st.metric(
                        label="Quantité",
                        value=f"{quantity} unité{'s' if quantity > 1 else ''}"
                    )

                with col_summary2:
                    st.metric(
                        label="Prix Unitaire",
                        value=f"{unit_price:.2f} €",
                        delta=f"{unit_price - suggested_price:.2f} €" if unit_price != suggested_price else None
                    )

                with col_summary3:
                    # Dynamic color based on total amount
                    if total < 50:
                        color = "#28a745"
                    elif total < 200:
                        color = "#ffc107"
                    else:
                        color = "#dc3545"

                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, {color} 0%, {color}aa 100%);
                                padding: 20px; border-radius: 15px; color: white; text-align: center;
                                box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                        <h2 style="margin: 0; color: white;">💰 TOTAL</h2>
                        <h1 style="margin: 5px 0; color: white; font-size: 2.5em;">{total:.2f} €</h1>
                        <p style="margin: 0; opacity: 0.9;">
                            {quantity} × {unit_price:.2f} €
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                # Additional visual feedback
                if total > 100:
                    st.info("💎 Commande importante ! Vérifiez les quantités avant de valider.")
                elif total < 10:
                    st.warning("⚠️ Commande de faible montant.")

            else:
                product_id = None
                unit_price = 0.01
                quantity = 1
                total = 0.01
        else:
            st.warning("Aucun produit actif trouvé dans la base de données")
            product_id = st.text_input("ID Produit (manuel)", placeholder="product_...")
            quantity = st.number_input("Quantité", min_value=1, value=1)
            unit_price = st.number_input("Prix unitaire (€)", min_value=0.01, value=1.0)
            total = quantity * unit_price

        # Part 2: Form submission (only the submission button)
        st.markdown("#### 📋 Finalisation")
        status = st.selectbox("Statut de la commande", ["pending", "confirmed", "shipped", "delivered", "cancelled"])

        with st.form("submit_order_form"):
            st.info(f"Résumé : {quantity} × {product_info.get('name', 'Produit') if 'product_info' in locals() else 'Produit'} = {total:.2f} €")

            submitted = st.form_submit_button("🚀 Créer la Commande")

            if submitted:
                if not customer_id:
                    st.error("L'ID client est requis")
                elif not product_id:
                    st.error("La sélection d'un produit est requise")
                else:
                    products = [{"product_id": product_id, "quantity": quantity, "price": unit_price}]

                    order_doc = OrderSchema.create_order(
                        customer_id=customer_id,
                        products=products,
                        total=total,
                        status=status
                    )

                    result = db_client.create(order_doc)
                    if result["success"]:
                        st.success(f"🎉 Commande créée avec succès ! ID: {order_doc['_id']}")
                        st.json(order_doc)
                    else:
                        st.error(f"❌ Échec de la création de commande : {result.get('error', 'Erreur inconnue')}")

def display_read_interface(db_client):
    """Display interface for reading documents"""
    st.subheader("📖 Read Documents")

    read_method = st.radio("Read Method", ["By ID", "Query by Type", "Advanced Search"])

    if read_method == "By ID":
        doc_id = st.text_input("Document ID", placeholder="e.g., product_12345...")

        if st.button("Get Document") and doc_id:
            result = db_client.read(doc_id)
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
    """Display user-friendly interface for updating documents"""
    st.subheader("✏️ Modifier des Documents")

    # Step 1: Select document type and specific document
    st.markdown("### 🔍 Sélection du Document à Modifier")

    doc_type = st.selectbox(
        "Type de document",
        ["Produit", "Client", "Commande"],
        key="update_doc_type_selector"
    )

    selected_doc = None
    selected_doc_id = None

    if doc_type == "Produit":
        all_products = get_all_products(db_client)
        if all_products:
            selected_product_display = st.selectbox(
                "Sélectionner un produit à modifier",
                list(all_products.keys()),
                key="update_product_selector"
            )
            if selected_product_display:
                selected_doc = all_products[selected_product_display]["document"]
                selected_doc_id = all_products[selected_product_display]["id"]
        else:
            st.warning("Aucun produit trouvé dans la base de données")

    elif doc_type == "Client":
        all_customers = get_all_customers(db_client)
        if all_customers:
            selected_customer_display = st.selectbox(
                "Sélectionner un client à modifier",
                list(all_customers.keys()),
                key="update_customer_selector"
            )
            if selected_customer_display:
                selected_doc = all_customers[selected_customer_display]["document"]
                selected_doc_id = all_customers[selected_customer_display]["id"]
        else:
            st.warning("Aucun client trouvé dans la base de données")

    elif doc_type == "Commande":
        all_orders = get_all_orders(db_client)
        if all_orders:
            selected_order_display = st.selectbox(
                "Sélectionner une commande à modifier",
                list(all_orders.keys()),
                key="update_order_selector"
            )
            if selected_order_display:
                selected_doc = all_orders[selected_order_display]["document"]
                selected_doc_id = all_orders[selected_order_display]["id"]
        else:
            st.warning("Aucune commande trouvée dans la base de données")

    # Step 2: Display current document info and update form
    if selected_doc and selected_doc_id:
        st.markdown("### 📝 Modification du Document")

        # Display current document info in a nice card
        st.markdown("#### 📋 Informations Actuelles")
        with st.expander("Voir le document complet", expanded=False):
            st.json(selected_doc)

        # Update forms based on document type
        if doc_type == "Produit":
            with st.form("update_product_form"):
                st.markdown("#### ✏️ Modifier le Produit")

                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Nom du produit *", value=selected_doc.get("name", ""))
                    category = st.selectbox(
                        "Catégorie *",
                        get_product_categories(db_client),
                        index=get_product_categories(db_client).index(selected_doc.get("category", "Electronics")) if selected_doc.get("category") in get_product_categories(db_client) else 0
                    )

                with col2:
                    price = st.number_input("Prix (€) *", value=selected_doc.get("price", 0.0), min_value=0.01, step=0.01)
                    status = st.selectbox("Statut",
                                        ["active", "inactive", "discontinued"],
                                        index=["active", "inactive", "discontinued"].index(selected_doc.get("status", "active")))

                description = st.text_area("Description", value=selected_doc.get("description", ""))

                submitted = st.form_submit_button("🚀 Mettre à Jour le Produit")

                if submitted and name and category:
                    from datetime import datetime, timezone
                    updates = {
                        "name": name,
                        "category": category,
                        "price": price,
                        "description": description,
                        "status": status,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "version": selected_doc.get("version", 1) + 1
                    }

                    result = db_client.update(selected_doc_id, updates)
                    if result["success"]:
                        st.success(f"🎉 Produit '{name}' mis à jour avec succès !")
                        # Show updated document
                        updated_result = db_client.read(selected_doc_id)
                        if updated_result["success"]:
                            st.markdown("#### ✅ Document Mis à Jour")
                            st.json(updated_result["document"])
                    else:
                        st.error(f"❌ Échec de la mise à jour : {result.get('error', 'Erreur inconnue')}")

        elif doc_type == "Client":
            with st.form("update_customer_form"):
                st.markdown("#### ✏️ Modifier le Client")

                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Nom du client *", value=selected_doc.get("name", ""))
                    email = st.text_input("Email *", value=selected_doc.get("email", ""))

                with col2:
                    phone = st.text_input("Téléphone", value=selected_doc.get("phone", ""))

                st.markdown("**Adresse**")
                address = selected_doc.get("address", {})
                col3, col4 = st.columns(2)
                with col3:
                    street = st.text_input("Rue", value=address.get("street", ""))
                    city = st.text_input("Ville", value=address.get("city", ""))
                with col4:
                    zip_code = st.text_input("Code postal", value=address.get("zip", ""))
                    country = st.text_input("Pays", value=address.get("country", ""))

                submitted = st.form_submit_button("🚀 Mettre à Jour le Client")

                if submitted and name and email:
                    from datetime import datetime, timezone
                    address_data = {}
                    if street: address_data["street"] = street
                    if city: address_data["city"] = city
                    if zip_code: address_data["zip"] = zip_code
                    if country: address_data["country"] = country

                    updates = {
                        "name": name,
                        "email": email,
                        "phone": phone,
                        "address": address_data,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "version": selected_doc.get("version", 1) + 1
                    }

                    result = db_client.update(selected_doc_id, updates)
                    if result["success"]:
                        st.success(f"🎉 Client '{name}' mis à jour avec succès !")
                        # Show updated document
                        updated_result = db_client.read(selected_doc_id)
                        if updated_result["success"]:
                            st.markdown("#### ✅ Document Mis à Jour")
                            st.json(updated_result["document"])
                    else:
                        st.error(f"❌ Échec de la mise à jour : {result.get('error', 'Erreur inconnue')}")

        elif doc_type == "Commande":
            with st.form("update_order_form"):
                st.markdown("#### ✏️ Modifier la Commande")

                col1, col2 = st.columns(2)
                with col1:
                    status = st.selectbox("Statut *",
                                        ["pending", "confirmed", "shipped", "delivered", "cancelled"],
                                        index=["pending", "confirmed", "shipped", "delivered", "cancelled"].index(selected_doc.get("status", "pending")))
                with col2:
                    total = st.number_input("Montant total (€) *", value=selected_doc.get("total", 0.0), min_value=0.01, step=0.01)

                # Display current products info
                products = selected_doc.get("products", [])
                if products:
                    st.markdown("**Produits dans la commande :**")
                    for i, product in enumerate(products):
                        st.write(f"• ID: {product.get('product_id', 'N/A')} | Quantité: {product.get('quantity', 0)} | Prix: {product.get('price', 0):.2f} €")

                submitted = st.form_submit_button("🚀 Mettre à Jour la Commande")

                if submitted:
                    from datetime import datetime, timezone
                    updates = {
                        "status": status,
                        "total": total,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "version": selected_doc.get("version", 1) + 1
                    }

                    result = db_client.update(selected_doc_id, updates)
                    if result["success"]:
                        st.success(f"🎉 Commande mise à jour avec succès !")
                        # Show updated document
                        updated_result = db_client.read(selected_doc_id)
                        if updated_result["success"]:
                            st.markdown("#### ✅ Document Mis à Jour")
                            st.json(updated_result["document"])
                    else:
                        st.error(f"❌ Échec de la mise à jour : {result.get('error', 'Erreur inconnue')}")

    else:
        st.info("👆 Sélectionnez un type de document et un élément spécifique pour commencer la modification.")

def display_delete_interface(db_client):
    """Display interface for deleting documents"""
    st.subheader("🗑️ Delete Documents")
    st.warning("⚠️ This action cannot be undone. Please be careful!")

    delete_method = st.radio("Delete Method", ["Single Document", "Bulk Delete by Query"])

    if delete_method == "Single Document":
        doc_id = st.text_input("Document ID to Delete", placeholder="e.g., product_12345...")

        # Preview document before deletion
        if doc_id and st.button("Preview Document"):
            result = db_client.read(doc_id)
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
                result = db_client.delete(st.session_state.delete_preview["_id"])
                if result["success"]:
                    st.success("Document supprimé avec succès !")
                    del st.session_state.delete_preview
                else:
                    st.error(f"Échec de la suppression : {result.get('error', 'Erreur inconnue')}")

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
                    result = db_client.delete(doc["_id"])
                    if result["success"]:
                        success_count += 1
                    else:
                        error_count += 1

                if error_count == 0:
                    st.success(f"{success_count} documents supprimés avec succès !")
                else:
                    st.warning(f"{success_count} documents supprimés, {error_count} échecs")

                del st.session_state.bulk_delete_docs
                del st.session_state.bulk_delete_query

if __name__ == "__main__":
    main()