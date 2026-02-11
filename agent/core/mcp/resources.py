from typing import Dict, List, Any

class MigrationResources:
    CODE_TEMPLATES = {
        "controller": """You are converting an ASP.NET controller to Spring Boot.
        Use @RestController, @RequestMapping, and constructor injection.
        Return ResponseEntity for all endpoints.""",
        "service": """You are converting an ASP.NET service to Spring Service.
        Use @Service annotation and repository pattern.""",
        "repository": """You are converting data access to Spring Data JPA.
        Extend JpaRepository and use JPQL for queries."""
    }
    
    def get_code_template(self, component_type: str) -> str:
        return self.CODE_TEMPLATES.get(component_type, "Convert this code to Java.")
    
    def get_database_context(self, table_schema: Dict) -> str:
        return f"Database table: {table_schema.get('table_name')}"
    
    def get_guidance_context(self, guidelines: Dict) -> str:
        return str(guidelines.get('coding_standards', ''))
