import json

class OracleVectorStore:
    def __init__(self, oracle_manager):
        self.db = oracle_manager
        self.embedding_dim = oracle_manager.config.vector_embedding_dimension
    
    def add_code_vector(
        self, component_id: str, file_path: str, component_type: str,
        component_name: str, namespace: str, code_content: str,
        embedding: List[float], metadata: Dict = None
    ):
        query = """
        INSERT INTO code_vectors (
            id, file_path, component_type, component_name,
            namespace, code_content, embedding, metadata
        ) VALUES (
            :id, :file_path, :component_type, :component_name,
            :namespace, :code_content, :embedding, :metadata
        )
        """
        vector_str = f"[{','.join(map(str, embedding))}]"
        params = {
            'id': component_id, 'file_path': file_path,
            'component_type': component_type, 'component_name': component_name,
            'namespace': namespace or '', 'code_content': code_content,
            'embedding': vector_str, 'metadata': json.dumps(metadata or {})
        }
        self.db.execute_update(query, params)
    
    def search_similar_code(
        self, query_embedding: List[float], top_k: int = 5,
        component_type: Optional[str] = None
    ) -> List[Dict]:
        vector_str = f"[{','.join(map(str, query_embedding))}]"
        where_clause = f"WHERE component_type = '{component_type}'" if component_type else ""
        query = f"""
        SELECT id, file_path, component_type, component_name, namespace,
               code_content, metadata, VECTOR_DISTANCE(embedding, :query_vector, COSINE) as distance
        FROM code_vectors {where_clause}
        ORDER BY VECTOR_DISTANCE(embedding, :query_vector, COSINE)
        FETCH FIRST :top_k ROWS ONLY
        """
        results = self.db.execute_query(query, {'query_vector': vector_str, 'top_k': top_k})
        return [
            {'id': r[0], 'file_path': r[1], 'component_type': r[2],
             'component_name': r[3], 'namespace': r[4], 'code_content': r[5],
             'metadata': json.loads(r[6]) if r[6] else {}, 'distance': float(r[7])}
            for r in results
        ]
    
    def get_component_by_id(self, component_id: str) -> Optional[Dict]:
        query = """
        SELECT id, file_path, component_type, component_name, namespace, code_content, metadata
        FROM code_vectors WHERE id = :id
        """
        results = self.db.execute_query(query, {'id': component_id})
        if results:
            r = results[0]
            return {'id': r[0], 'file_path': r[1], 'component_type': r[2],
                    'component_name': r[3], 'namespace': r[4], 'code_content': r[5],
                    'metadata': json.loads(r[6]) if r[6] else {}}
        return None
