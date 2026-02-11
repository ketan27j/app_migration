import json
from typing import List, Dict, Optional

class OracleGraphStore:
    def __init__(self, oracle_manager):
        self.db = oracle_manager
    
    def create_component_node(
        self, component_id: str, name: str, component_type: str,
        namespace: str = None, file_path: str = None, metadata: Dict = None
    ):
        query = """
        MERGE INTO code_components c
        USING (SELECT :id as id FROM dual) d ON (c.id = d.id)
        WHEN NOT MATCHED THEN
            INSERT (id, name, type, namespace, file_path, metadata)
            VALUES (:id, :name, :type, :namespace, :file_path, :metadata)
        WHEN MATCHED THEN UPDATE SET name=:name, type=:type, namespace=:namespace, file_path=:file_path, metadata=:metadata
        """
        params = {'id': component_id, 'name': name, 'type': component_type,
                  'namespace': namespace or '', 'file_path': file_path or '',
                  'metadata': json.dumps(metadata or {})}
        self.db.execute_update(query, params)
    
    def create_dependency(
        self, from_id: str, to_id: str, dependency_type: str = 'DEPENDS_ON',
        strength: float = 1.0, metadata: Dict = None
    ):
        query = """
        MERGE INTO code_dependencies d
        USING (SELECT :from_id as from_id, :to_id as to_id, :dep_type as dep_type FROM dual) s
        ON (d.from_id = s.from_id AND d.to_id = s.to_id AND d.dependency_type = s.dep_type)
        WHEN NOT MATCHED THEN INSERT (from_id, to_id, dependency_type, strength, metadata)
            VALUES (:from_id, :to_id, :dep_type, :strength, :metadata)
        WHEN MATCHED THEN UPDATE SET strength=:strength, metadata=:metadata
        """
        params = {'from_id': from_id, 'to_id': to_id, 'dep_type': dependency_type,
                  'strength': strength, 'metadata': json.dumps(metadata or {})}
        self.db.execute_update(query, params)
    
    def get_dependencies(self, component_id: str, max_depth: int = 1) -> List[Dict]:
        if max_depth == 1:
            query = """
            SELECT c.id, c.name, c.type, c.namespace, c.file_path, d.dependency_type, d.strength
            FROM code_components c JOIN code_dependencies d ON c.id = d.to_id
            WHERE d.from_id = :component_id ORDER BY d.strength DESC
            """
            results = self.db.execute_query(query, {'component_id': component_id})
        else:
            query = f"""
            WITH RECURSIVE dep_tree AS (
                SELECT d.to_id as id, 1 as depth FROM code_dependencies d WHERE d.from_id = :component_id
                UNION ALL
                SELECT d.to_id, dt.depth + 1 FROM code_dependencies d JOIN dep_tree dt ON d.from_id = dt.id WHERE dt.depth < :max_depth
            )
            SELECT DISTINCT c.id, c.name, c.type, c.namespace, c.file_path, 'DEPENDS_ON' as dependency_type, 1.0 as strength
            FROM code_components c JOIN dep_tree dt ON c.id = dt.id
            """
            results = self.db.execute_query(query, {'component_id': component_id, 'max_depth': max_depth})
        return [{'id': r[0], 'name': r[1], 'type': r[2], 'namespace': r[3], 'file_path': r[4],
                 'dependency_type': r[5], 'strength': float(r[6])} for r in results]
    
    def get_dependents(self, component_id: str) -> List[Dict]:
        query = """
        SELECT c.id, c.name, c.type, c.namespace, c.file_path, d.dependency_type, d.strength
        FROM code_components c JOIN code_dependencies d ON c.id = d.from_id
        WHERE d.to_id = :component_id ORDER BY d.strength DESC
        """
        results = self.db.execute_query(query, {'component_id': component_id})
        return [{'id': r[0], 'name': r[1], 'type': r[2], 'namespace': r[3], 'file_path': r[4],
                 'dependency_type': r[5], 'strength': float(r[6])} for r in results]
