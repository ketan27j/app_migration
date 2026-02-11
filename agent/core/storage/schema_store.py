import json
from typing import List, Dict, Optional

class OracleSchemaStore:
    def __init__(self, oracle_manager):
        self.db = oracle_manager
    
    def add_table_schema(self, schema_name: str, table_name: str,
                         columns: List[Dict], indexes: List[Dict] = None,
                         relationships: List[Dict] = None):
        query = """
        MERGE INTO db_schema_reference s
        USING (SELECT :schema_name as schema_name, :table_name as table_name FROM dual) src
        ON (s.schema_name = src.schema_name AND s.table_name = src.table_name)
        WHEN NOT MATCHED THEN INSERT (schema_name, table_name, column_definitions, indexes, relationships)
            VALUES (:schema_name, :table_name, :columns, :indexes, :relationships)
        WHEN MATCHED THEN UPDATE SET column_definitions=:columns, indexes=:indexes, relationships=:relationships
        """
        params = {'schema_name': schema_name, 'table_name': table_name,
                  'columns': json.dumps(columns), 'indexes': json.dumps(indexes or []),
                  'relationships': json.dumps(relationships or [])}
        self.db.execute_update(query, params)
    
    def add_stored_procedure(self, schema_name: str, proc_name: str,
                             parameters: List[Dict], definition: str):
        query = """
        MERGE INTO stored_procedures p
        USING (SELECT :schema_name as schema_name, :proc_name as proc_name FROM dual) src
        ON (p.schema_name = src.schema_name AND p.proc_name = src.proc_name)
        WHEN NOT MATCHED THEN INSERT (schema_name, proc_name, parameters, definition)
            VALUES (:schema_name, :proc_name, :parameters, :definition)
        WHEN MATCHED THEN UPDATE SET parameters=:parameters, definition=:definition
        """
        params = {'schema_name': schema_name, 'proc_name': proc_name,
                  'parameters': json.dumps(parameters), 'definition': definition}
        self.db.execute_update(query, params)
    
    def get_table_schema(self, table_name: str) -> Optional[Dict]:
        query = """
        SELECT schema_name, table_name, column_definitions, indexes, relationships
        FROM db_schema_reference WHERE table_name = :table_name
        """
        results = self.db.execute_query(query, {'table_name': table_name})
        if results:
            r = results[0]
            return {'schema_name': r[0], 'table_name': r[1],
                    'columns': json.loads(r[2]), 'indexes': json.loads(r[3]) if r[3] else [],
                    'relationships': json.loads(r[4]) if r[4] else []}
        return None
    
    def get_stored_procedure(self, proc_name: str) -> Optional[Dict]:
        query = "SELECT schema_name, proc_name, parameters, definition FROM stored_procedures WHERE proc_name = :proc_name"
        results = self.db.execute_query(query, {'proc_name': proc_name})
        if results:
            r = results[0]
            return {'schema_name': r[0], 'proc_name': r[1],
                    'parameters': json.loads(r[2]), 'definition': r[3]}
        return None
    
    def search_tables_by_keyword(self, keyword: str) -> List[Dict]:
        query = """
        SELECT schema_name, table_name, column_definitions FROM db_schema_reference
        WHERE UPPER(table_name) LIKE UPPER('%' || :keyword || '%')
           OR JSON_EXISTS(column_definitions, '$[*].name ? (@ like_regex $pattern flag "i")' PASSING :keyword AS "pattern")
        """
        results = self.db.execute_query(query, {'keyword': keyword})
        return [{'schema_name': r[0], 'table_name': r[1], 'columns': json.loads(r[2])} for r in results]
