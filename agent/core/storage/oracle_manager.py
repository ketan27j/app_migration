import oracledb
from typing import List, Dict, Optional, Any
import json
from contextlib import contextmanager

class OracleManager:
    def __init__(self, config):
        self.config = config
        self.pool = self._create_pool()
        from agent.core.storage.vector_store import OracleVectorStore
        from agent.core.storage.graph_store import OracleGraphStore
        from agent.core.storage.schema_store import OracleSchemaStore
        self.vector_store = OracleVectorStore(self)
        self.graph_store = OracleGraphStore(self)
        self.schema_store = OracleSchemaStore(self)
    
    def _create_pool(self):
        pool = oracledb.create_pool(
            user=self.config.username,
            password=self.config.password,
            dsn=f"{self.config.host}:{self.config.port}/{self.config.service_name}",
            min=2, max=self.config.pool_size, increment=1
        )
        return pool
    
    @contextmanager
    def get_connection(self):
        conn = self.pool.acquire()
        try:
            yield conn
        finally:
            self.pool.release(conn)
    
    def execute_query(self, query: str, params: Dict = None) -> List[tuple]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results
    
    def execute_update(self, query: str, params: Dict = None) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rowcount = cursor.rowcount
            conn.commit()
            cursor.close()
            return rowcount
    
    def execute_many(self, query: str, params_list: List[Dict]) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            rowcount = cursor.rowcount
            conn.commit()
            cursor.close()
            return rowcount
    
    def close(self):
        if self.pool:
            self.pool.close()
