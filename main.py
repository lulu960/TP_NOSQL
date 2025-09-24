#!/usr/bin/env python3
"""
Main entry point for the CouchDB project
Provides a unified interface to all project components
"""

import os
import sys
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_couchdb():
    """Setup CouchDB database"""
    from setup_couchdb import CouchDBSetup
    setup = CouchDBSetup()
    setup.run_setup()

def run_etl():
    """Run ETL process"""
    sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
    from etl import main as etl_main
    etl_main()

def run_analytics():
    """Run analytics examples"""
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    from analytics import run_sample_analytics, setup_analytics

    print("Setting up analytics views...")
    setup_analytics()

    print("\nRunning sample analytics...")
    run_sample_analytics()

def run_admin():
    """Run admin interface"""
    sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))
    # Import and run admin with remaining arguments
    from admin import main as admin_main
    # Remove 'admin' from sys.argv so admin.main() gets correct args
    sys.argv = ['admin.py'] + sys.argv[2:]
    admin_main()

def run_webapp():
    """Run Streamlit webapp"""
    import subprocess
    webapp_path = os.path.join(os.path.dirname(__file__), 'webapp', 'app.py')
    print(f"Starting Streamlit webapp...")
    print(f"Open your browser to http://localhost:8501")
    subprocess.run(['streamlit', 'run', webapp_path])

def run_tests():
    """Run tests"""
    import subprocess
    tests_path = os.path.join(os.path.dirname(__file__), 'tests')
    print("Running unit tests...")
    result = subprocess.run(['python', '-m', 'pytest', tests_path, '-v'],
                          capture_output=False)
    return result.returncode == 0

def show_status():
    """Show project status"""
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    from database import CouchDBClient

    print("CouchDB Project Status")
    print("=" * 40)

    try:
        client = CouchDBClient()

        # Test connection
        info_result = client.get_database_info()
        if info_result['success']:
            info = info_result['info']
            print("✓ CouchDB Connection: OK")
            print(f"  Database: {info.get('db_name', 'N/A')}")
            print(f"  Documents: {info.get('doc_count', 0)}")
            print(f"  Size: {info.get('data_size', 0) / 1024 / 1024:.2f} MB")
        else:
            print("✗ CouchDB Connection: FAILED")
            print(f"  Error: {info_result.get('error', 'Unknown error')}")
            return

        # Check document types
        doc_types = ['product', 'customer', 'order', 'analytics_event']
        print("\nDocument Counts by Type:")

        for doc_type in doc_types:
            result = client.find({"type": doc_type}, limit=1000)
            if result['success']:
                count = len(result['documents'])
                print(f"  {doc_type}: {count}")
            else:
                print(f"  {doc_type}: ERROR")

        # Check if webapp dependencies are available
        print("\nDependency Status:")
        try:
            import streamlit
            print("✓ Streamlit: Available")
        except ImportError:
            print("✗ Streamlit: Not installed")

        try:
            import pytest
            print("✓ Pytest: Available")
        except ImportError:
            print("✗ Pytest: Not installed")

        print("\nQuick Start Commands:")
        print("  python main.py setup    - Setup CouchDB")
        print("  python main.py etl      - Load sample data")
        print("  python main.py webapp   - Start web dashboard")
        print("  python main.py test     - Run tests")

    except Exception as e:
        print(f"✗ Status check failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure CouchDB is running")
        print("2. Check your .env configuration")
        print("3. Run 'python main.py setup' first")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='CouchDB Project - Unified Interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py setup          Setup CouchDB database
  python main.py etl            Run ETL process to load data
  python main.py analytics      Run analytics examples
  python main.py webapp         Start Streamlit web application
  python main.py admin stats    Show database statistics
  python main.py test           Run unit tests
  python main.py status         Show project status
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup CouchDB database')

    # ETL command
    etl_parser = subparsers.add_parser('etl', help='Run ETL process')

    # Analytics command
    analytics_parser = subparsers.add_parser('analytics', help='Run analytics examples')

    # Admin command (pass through remaining args)
    admin_parser = subparsers.add_parser('admin', help='Run admin commands')
    admin_parser.add_argument('admin_args', nargs=argparse.REMAINDER, help='Admin command arguments')

    # Webapp command
    webapp_parser = subparsers.add_parser('webapp', help='Start Streamlit web application')

    # Test command
    test_parser = subparsers.add_parser('test', help='Run unit tests')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show project status')

    args = parser.parse_args()

    if not args.command:
        # Show status by default
        show_status()
        return

    print(f"CouchDB Project - Running: {args.command}")
    print("-" * 50)

    try:
        if args.command == 'setup':
            setup_couchdb()

        elif args.command == 'etl':
            run_etl()

        elif args.command == 'analytics':
            run_analytics()

        elif args.command == 'admin':
            run_admin()

        elif args.command == 'webapp':
            run_webapp()

        elif args.command == 'test':
            success = run_tests()
            if not success:
                print("\nSome tests failed!")
                sys.exit(1)
            else:
                print("\nAll tests passed!")

        elif args.command == 'status':
            show_status()

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\nOperation interrupted by user")

    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()