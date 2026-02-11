#!/usr/bin/env python3

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.orchestrator import MigrationOrchestrator
from agent.config.settings import settings

def main():
    parser = argparse.ArgumentParser(description='ASP.NET to Java/Angular Migration Agent')
    parser.add_argument('--test-connection', action='store_true', help='Test connections')
    parser.add_argument('--component', type=str, help='Migrate specific component')
    parser.add_argument('--type', type=str, choices=['controller', 'service', 'model', 'all'], default='all')
    args = parser.parse_args()
    
    if args.test_connection:
        test_connections()
        return
    
    orchestrator = MigrationOrchestrator()
    try:
        if args.component:
            print(f"Migrating component: {args.component}")
            orchestrator._migrate_controller(orchestrator._generate_id(args.component))
        else:
            orchestrator.run_migration()
    finally:
        orchestrator.close()

def test_connections():
    print("Testing connections...")
    print("-" * 60)
    
    try:
        from agent.core.integrations.bitbucket_client import BitbucketClient
        client = BitbucketClient(workspace=settings.migration.source_workspace, token=settings.bitbucket.token)
        files = client.get_repository_tree(settings.migration.source_repo_slug, settings.migration.source_branch)
        print(f"✓ Bitbucket connected - found {len(files)} files")
    except Exception as e:
        print(f"✗ Bitbucket connection failed: {e}")
    
    try:
        from agent.core.storage.oracle_manager import OracleManager
        oracle = OracleManager(settings.oracle)
        oracle.execute_query("SELECT 1 FROM dual")
        oracle.close()
        print("✓ Oracle connected")
    except Exception as e:
        print(f"✗ Oracle connection failed: {e}")
    
    try:
        from agent.core.integrations.llm_client import LocalLLMClient
        llm = LocalLLMClient(settings.llm)
        if llm.test_connection():
            print("✓ LLM connected")
        else:
            print("✗ LLM connection failed")
    except Exception as e:
        print(f"✗ LLM connection failed: {e}")
    
    try:
        import pyodbc
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={settings.sqlserver.host},{settings.sqlserver.port};DATABASE={settings.sqlserver.database};UID={settings.sqlserver.username};PWD={settings.sqlserver.password}"
        conn = pyodbc.connect(conn_str)
        conn.close()
        print("✓ SQL Server connected")
    except Exception as e:
        print(f"✗ SQL Server connection failed: {e}")
    
    print("-" * 60)
    print("Connection tests complete")

if __name__ == "__main__":
    main()
