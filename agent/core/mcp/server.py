from typing import List, Dict, Optional
from mcp.server import Server
from mcp.types import Resource, Tool

class MigrationMCPServer:
    def __init__(self, vector_store, graph_store):
        self.server = Server("migration-context")
        self.vector_store = vector_store
        self.graph_store = graph_store
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.server.list_resources()
        async def list_resources():
            return [
                Resource(
                    uri="code://old-app/controllers",
                    name="ASP.NET Controllers",
                    description="All controller code with business logic"
                ),
                Resource(
                    uri="docs://functional-specs",
                    name="Functional Documentation",
                    description="Business requirements and API specifications"
                ),
                Resource(
                    uri="schema://database",
                    name="Database Schema",
                    description="SQL Server schema and relationships"
                )
            ]
        
        @self.server.read_resource()
        async def read_resource(uri):
            if uri.startswith("code://"):
                return await self.get_code_context(uri)
            elif uri.startswith("docs://"):
                return await self.get_doc_context(uri)
            elif uri.startswith("schema://"):
                return await self.get_schema_context(uri)
            return None
    
    async def get_code_context(self, uri):
        query = uri.replace("code://", "")
        relevant_code = self.vector_store.search_similar_code(
            self._get_embedding_for_query(query), k=10
        )
        dependencies = self.graph_store.get_dependencies(query)
        return {"code": relevant_code, "dependencies": dependencies}
    
    async def get_doc_context(self, uri):
        doc_type = uri.replace("docs://", "")
        return {"docs": f"Documentation for {doc_type}"}
    
    async def get_schema_context(self, uri):
        return {"schema": "SQL Server schema context"}
    
    def _get_embedding_for_query(self, query: str) -> List[float]:
        return [0.0] * 1536
    
    async def run(self):
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())
