import os
import yaml
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class OracleConfig(BaseModel):
    host: str
    port: int
    service_name: str
    username: str
    password: str
    pool_size: int = 10
    vector_embedding_dimension: int = Field(default=1536, alias="vector.embedding_dimension")
    vector_distance_metric: str = Field(default="COSINE", alias="vector.distance_metric")

class SqlServerConfig(BaseModel):
    host: str
    port: int
    database: str
    username: str
    password: str

class BitbucketConfig(BaseModel):
    base_url: str = "https://api.bitbucket.org/2.0"
    token: str
    rate_limit_delay: float = 1.0

class LLMConfig(BaseModel):
    base_url: str
    api_type: str = "openai"
    auth_type: str = "bearer"
    token: str
    verify_ssl: bool = True
    cert_path: str = None
    model_name: str
    max_tokens: int = 4000
    temperature: float = 0.2
    embedding_model: str
    embedding_url: str = None
    custom_headers: Dict[str, str] = {}

class MigrationConfig(BaseModel):
    source_workspace: str = Field(alias="source.workspace")
    source_repo_slug: str = Field(alias="source.repo_slug")
    source_branch: str = Field(alias="source.branch")
    source_path_pattern: str = Field(alias="source.path_pattern")
    target_backend_path: str = Field(alias="target.backend.path")
    target_backend_framework: str = Field(alias="target.backend.framework")
    target_backend_package: str = Field(alias="target.backend.package_base")
    target_frontend_path: str = Field(alias="target.frontend.path")
    target_frontend_framework: str = Field(alias="target.frontend.framework")

class Settings:
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = Path(config_path)
        self.config_data = self._load_config()
        self.oracle = self._parse_oracle_config()
        self.sqlserver = self._parse_sqlserver_config()
        self.bitbucket = self._parse_bitbucket_config()
        self.llm = self._parse_llm_config()
        self.migration = self._parse_migration_config()
    
    def _load_config(self) -> Dict[str, Any]:
        with open(self.config_path, 'r') as f:
            content = f.read()
        import re
        def replace_env_var(match):
            var_name = match.group(1)
            return os.getenv(var_name, match.group(0))
        content = re.sub(r'\$\{(\w+)\}', replace_env_var, content)
        return yaml.safe_load(content)
    
    def _parse_oracle_config(self) -> OracleConfig:
        oracle_data = self.config_data['oracle']
        flattened = {
            **oracle_data,
            'vector.embedding_dimension': oracle_data.get('vector', {}).get('embedding_dimension', 1536),
            'vector.distance_metric': oracle_data.get('vector', {}).get('distance_metric', 'COSINE')
        }
        return OracleConfig(**flattened)
    
    def _parse_sqlserver_config(self) -> SqlServerConfig:
        return SqlServerConfig(**self.config_data['sqlserver'])
    
    def _parse_bitbucket_config(self) -> BitbucketConfig:
        return BitbucketConfig(**self.config_data['bitbucket'])
    
    def _parse_llm_config(self) -> LLMConfig:
        llm_data = self.config_data['llm']
        return LLMConfig(**llm_data)
    
    def _parse_migration_config(self) -> MigrationConfig:
        migration_data = self.config_data['migration']
        flattened = {
            'source.workspace': migration_data['source']['workspace'],
            'source.repo_slug': migration_data['source']['repo_slug'],
            'source.branch': migration_data['source']['branch'],
            'source.path_pattern': migration_data['source']['path_pattern'],
            'target.backend.path': migration_data['target']['backend']['path'],
            'target.backend.framework': migration_data['target']['backend']['framework'],
            'target.backend.package_base': migration_data['target']['backend']['package_base'],
            'target.frontend.path': migration_data['target']['frontend']['path'],
            'target.frontend.framework': migration_data['target']['frontend']['framework']
        }
        return MigrationConfig(**flattened)

settings = Settings()
