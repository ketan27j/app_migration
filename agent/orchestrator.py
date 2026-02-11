import os
import hashlib
from typing import Dict, List, Optional
from pathlib import Path

from agent.config.settings import settings
from agent.core.integrations.bitbucket_client import BitbucketClient
from agent.core.integrations.llm_client import LocalLLMClient
from agent.core.storage.oracle_manager import OracleManager
from agent.core.parsers.csharp_parser import CSharpParser
from agent.core.parsers.guideline_parser import GuidelineParser
from agent.core.generators.java_generator import JavaGenerator
from agent.core.generators.angular_generator import AngularGenerator
import pyodbc
import json

class MigrationOrchestrator:
    def __init__(self):
        self.bitbucket = BitbucketClient(
            workspace=settings.migration.source_workspace,
            token=settings.bitbucket.token
        )
        self.llm = LocalLLMClient(settings.llm)
        self.oracle = OracleManager(settings.oracle)
        self.parser = CSharpParser()
        self.guideline_parser = GuidelineParser()
        self.java_generator = JavaGenerator(settings.migration.target_backend_package)
        self.angular_generator = AngularGenerator(settings.migration.target_frontend_path)
        self.guidelines = None
        self.schema_context = None
    
    def run_migration(self):
        print("=" * 60)
        print("MIGRATION AGENT - Starting")
        print("=" * 60)
        
        print("\n[1/6] Fetching code from Bitbucket...")
        code_files = self._fetch_old_code()
        print(f"✓ Fetched {len(code_files)} files")
        
        print("\n[2/6] Parsing code and storing in Oracle...")
        self._parse_and_store_code(code_files)
        print(f"✓ Stored {len(code_files)} components")
        
        print("\n[3/6] Extracting SQL Server schema...")
        self._extract_sql_server_schema()
        print("✓ Schema extracted and stored as context")
        
        print("\n[4/6] Parsing coding guidelines...")
        self._parse_guidelines()
        print("✓ Guidelines loaded")
        
        print("\n[5/6] Migrating components...")
        self._migrate_all_components()
        print("✓ Components migrated")
        
        print("\n[6/6] Generating migration report...")
        self._generate_report()
        
        print("\n" + "=" * 60)
        print("MIGRATION COMPLETE")
        print("=" * 60)
    
    def _fetch_old_code(self) -> List[Dict]:
        return self.bitbucket.fetch_code_files(
            repo_slug=settings.migration.source_repo_slug,
            branch=settings.migration.source_branch,
            path_pattern=settings.migration.source_path_pattern
        )
    
    def _parse_and_store_code(self, code_files: List[Dict]):
        for file_data in code_files:
            component = self.parser.parse_code(file_data['content'], file_data['path'])
            component_id = self._generate_id(file_data['path'])
            embedding = self.llm.generate_embedding(component.code)
            
            self.oracle.vector_store.add_code_vector(
                component_id=component_id,
                file_path=component.file_path,
                component_type=component.type,
                component_name=component.name,
                namespace=component.namespace,
                code_content=component.code,
                embedding=embedding,
                metadata={'methods': component.methods, 'properties': component.properties, 'dependencies': component.dependencies}
            )
            
            self.oracle.graph_store.create_component_node(
                component_id=component_id, name=component.name,
                component_type=component.type, namespace=component.namespace, file_path=component.file_path
            )
            
            for dep in component.dependencies:
                dep_id = self._generate_id(dep)
                self.oracle.graph_store.create_dependency(from_id=component_id, to_id=dep_id, dependency_type='USES')
    
    def _extract_sql_server_schema(self):
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={settings.sqlserver.host},{settings.sqlserver.port};"
            f"DATABASE={settings.sqlserver.database};"
            f"UID={settings.sqlserver.username};"
            f"PWD={settings.sqlserver.password}"
        )
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.TABLE_SCHEMA, t.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE, c.IS_NULLABLE, c.CHARACTER_MAXIMUM_LENGTH
            FROM INFORMATION_SCHEMA.TABLES t
            JOIN INFORMATION_SCHEMA.COLUMNS c ON t.TABLE_NAME = c.TABLE_NAME
            WHERE t.TABLE_TYPE = 'BASE TABLE'
            ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION
        """)
        
        tables = {}
        for row in cursor.fetchall():
            table_key = f"{row[0]}.{row[1]}"
            if table_key not in tables:
                tables[table_key] = {'schema': row[0], 'name': row[1], 'columns': []}
            tables[table_key]['columns'].append({'name': row[2], 'type': row[3], 'nullable': row[4] == 'YES', 'max_length': row[5]})
        
        for table_key, table_data in tables.items():
            self.oracle.schema_store.add_table_schema(table_data['schema'], table_data['name'], table_data['columns'])
        
        cursor.execute("SELECT ROUTINE_SCHEMA, ROUTINE_NAME, ROUTINE_DEFINITION FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_TYPE = 'PROCEDURE'")
        for row in cursor.fetchall():
            self.oracle.schema_store.add_stored_procedure(row[0], row[1], [], row[2])
        
        conn.close()
        self.schema_context = tables
    
    def _parse_guidelines(self):
        backend_readme_path = os.path.join(settings.migration.target_backend_path, "README.md")
        frontend_readme_path = os.path.join(settings.migration.target_frontend_path, "README.md")
        
        backend_guidelines = {}
        if os.path.exists(backend_readme_path):
            with open(backend_readme_path, 'r') as f:
                backend_guidelines = self.guideline_parser.extract_guidelines(f.read())
        
        frontend_guidelines = {}
        if os.path.exists(frontend_readme_path):
            with open(frontend_readme_path, 'r') as f:
                frontend_guidelines = self.guideline_parser.extract_guidelines(f.read())
        
        self.guidelines = {'backend': backend_guidelines, 'frontend': frontend_guidelines}
    
    def _migrate_all_components(self):
        controllers = self.oracle.db.execute_query("SELECT id, component_name, file_path FROM code_vectors WHERE component_type = 'controller'")
        for row in controllers:
            component_id, name, file_path = row
            print(f"  Migrating controller: {name}")
            try:
                self._migrate_controller(component_id)
                print(f"  ✓ {name}")
            except Exception as e:
                print(f"  ✗ {name}: {e}")
    
    def _migrate_controller(self, component_id: str):
        component = self.oracle.vector_store.get_component_by_id(component_id)
        if not component:
            raise ValueError(f"Component {component_id} not found")
        
        deps = self.oracle.graph_store.get_dependencies(component_id)
        context = self._build_migration_context(component, deps)
        java_code = self._generate_java_controller(component, context)
        self._save_generated_code('controller', component['component_name'], java_code)
        
        self.oracle.db.execute_update("""
            INSERT INTO migration_logs (component_id, component_type, migration_status, start_time, end_time, generated_code)
            VALUES (:id, :type, :status, SYSTIMESTAMP, SYSTIMESTAMP, :code)
        """, {'id': component_id, 'type': 'controller', 'status': 'SUCCESS', 'code': java_code})
    
    def _build_migration_context(self, component: Dict, dependencies: List[Dict]) -> Dict:
        related_tables = []
        for dep in dependencies:
            if 'Repository' in dep['name']:
                entity = dep['name'].replace('Repository', '')
                table_schema = self.oracle.schema_store.get_table_schema(entity)
                if table_schema:
                    related_tables.append(table_schema)
        return {'dependencies': dependencies, 'guidelines': self.guidelines['backend'], 'database_schema': related_tables, 'package_base': settings.migration.target_backend_package}
    
    def _generate_java_controller(self, component: Dict, context: Dict) -> str:
        return self.java_generator.generate_controller(component, context)
    
    def _save_generated_code(self, component_type: str, component_name: str, code: str):
        if component_type == 'controller':
            base_path = Path(settings.migration.target_backend_path)
            package_path = settings.migration.target_backend_package.replace('.', '/')
            output_dir = base_path / "src" / "main" / "java" / package_path / "controller"
        else:
            output_dir = Path(settings.migration.target_backend_path) / "src" / "main" / "java"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        import re
        class_match = re.search(r'public\s+class\s+(\w+)', code)
        class_name = class_match.group(1) if class_match else component_name
        
        output_file = output_dir / f"{class_name}.java"
        with open(output_file, 'w') as f:
            f.write(code)
        print(f"    Saved: {output_file}")
    
    def _generate_report(self):
        results = self.oracle.db.execute_query("""
            SELECT component_type, migration_status, COUNT(*) as count
            FROM migration_logs GROUP BY component_type, migration_status ORDER BY component_type, migration_status
        """)
        print("\nMigration Summary:")
        print("-" * 40)
        for row in results:
            print(f"{row[0]}: {row[1]} = {row[2]}")
    
    def _generate_id(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()
    
    def close(self):
        self.oracle.close()
