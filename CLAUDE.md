# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a CouchDB analytics project with Python that demonstrates complete data pipeline operations including ETL, analytics, and web dashboard visualization. The project uses CouchDB as the primary database with Python for application logic and Streamlit for the web interface.

## Essential Commands

### Setup and Database Initialization
```bash
# Setup CouchDB database, users, and indexes
python main.py setup

# Alternative: Use simple setup script (avoids Unicode issues on Windows)
python simple_setup.py

# Setup analytics MapReduce views
python setup_analytics.py
```

### Data Operations
```bash
# Run complete ETL pipeline to populate database with sample data
python main.py etl

# Alternative: Direct ETL script
python scripts/etl.py
```

### Running the Application
```bash
# Launch Streamlit web dashboard (http://localhost:8501)
python main.py webapp
# OR
streamlit run webapp/app.py

# Run analytics examples and demonstrations
python main.py analytics
```

### Development and Testing
```bash
# Run all tests
python main.py test
# OR
python -m pytest tests/ -v

# Run specific tests
python -m pytest tests/test_database.py -v

# Test analytics functionality
python test_analytics.py
```

### Database Administration
```bash
# View database statistics
python main.py admin stats

# Export data to JSON/CSV
python main.py admin export data/backup.json
python main.py admin export data/export.csv --format csv

# Import data
python main.py admin import data/import.json
```

## Architecture and Code Structure

### Core Components

1. **Database Layer** (`src/database.py`)
   - `CouchDBClient`: Main CRUD operations class
   - Handles all HTTP requests to CouchDB API
   - Manages authentication and sessions
   - Provides create, read, update, delete, find operations

2. **Data Models** (`src/models.py`)
   - Schema definitions for all document types
   - `ProductSchema`, `CustomerSchema`, `OrderSchema`, `AnalyticsEventSchema`
   - Handles document structure and validation
   - Automatic timestamp and ID generation

3. **Analytics Engine** (`src/analytics.py`)
   - `AnalyticsEngine`: Advanced querying and analytics
   - Mango query examples and complex aggregations
   - MapReduce views for sales_by_month, products_by_category
   - KPI calculations and reporting functions

4. **ETL Pipeline** (`scripts/etl.py`)
   - Data processing, cleaning, and enrichment
   - Bulk document insertion
   - Sample data generation for testing
   - Error handling and data validation

5. **Web Dashboard** (`webapp/app.py`)
   - Streamlit-based web interface
   - KPI cards, charts, and interactive visualizations
   - Data explorer and raw data viewer
   - Uses matplotlib and plotly for charts

6. **Administration Tools** (`scripts/admin.py`)
   - Database backup/restore operations
   - Data export/import utilities
   - User management functions

### Key Architectural Patterns

**Document Structure**: All documents follow a consistent schema with `type`, `created_at`, `updated_at`, and `version` fields. Documents are denormalized for CouchDB performance.

**Analytics Strategy**: Two-tier approach using both Mango queries for simple operations and MapReduce views for complex aggregations. Views are pre-built and cached by CouchDB.

**Error Handling**: All operations return consistent `{"success": boolean, "data/error": any, "message": string}` response format.

**Configuration**: Environment variables in `.env` file control all database connections and user credentials.

## Important Implementation Details

### CouchDB Connection
- Default connection: `http://localhost:5984`
- Database name: `tp_database`
- Authentication uses admin/analyst users with role-based access
- All HTTP operations go through `requests.Session` with basic auth

### MapReduce Views
- Views must be created before use with `setup_analytics_views()`
- Views are stored in `_design/analytics` document
- Key pattern: `[year, month]` for time-series data
- Views return `{"rows": [...]}` structure

### Data Flow
1. ETL generates sample data → CouchDB bulk insert
2. Analytics engine queries database → processes results
3. Streamlit dashboard calls analytics functions → displays visualizations
4. All operations use the same `CouchDBClient` instance

### Common Issues and Solutions

**Unicode Character Issues**: Windows command prompt cannot display Unicode characters (✓, ✗, 🎉). Always use plain text in print statements for Windows compatibility.

**MapReduce View Creation**: Views must be explicitly created and may take time to build. Always call `setup_analytics_views()` after database setup.

**Streamlit Caching**: Use `_analytics_engine` parameter naming (with underscore prefix) in cached functions to avoid unhashable object errors.

**Database State**: Always verify database exists before running ETL. Use `simple_setup.py` if full setup fails with Unicode errors.

## Environment Configuration

Required `.env` variables:
```
COUCHDB_URL=http://localhost:5984
COUCHDB_USER=admin
COUCHDB_PASSWORD=adminpass
DATABASE_NAME=tp_database
ADMIN_USER=admin
ADMIN_PASSWORD=adminpass
ANALYST_USER=analyst
ANALYST_PASSWORD=analystpass
```

## Dependencies

Key Python packages (see `requirements.txt`):
- `requests`: HTTP client for CouchDB API
- `streamlit`: Web dashboard framework
- `pandas`: Data processing in ETL
- `plotly`, `matplotlib`: Visualization libraries
- `pytest`: Testing framework
- `python-dotenv`: Environment variable management

## Quick Development Workflow

1. Ensure CouchDB is running: `curl http://localhost:5984`
2. Setup database: `python main.py setup`
3. Load sample data: `python main.py etl`
4. Launch dashboard: `python main.py webapp`
5. Run tests: `python main.py test`

For debugging analytics issues, use `test_analytics.py` to verify MapReduce views and data structure.