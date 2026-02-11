# Migration Agent Implementation Guide
## Oracle + Bitbucket + Local LLM Configuration

---

## 1. Environment Setup

### 1.1 Prerequisites

```bash
# Required software
- Python 3.10+
- Oracle Database 23ai
- SQL Server (existing - no migration needed)
- Bitbucket account with API access
- Local LLM server (llama.cpp, vLLM, or similar)
```

### 1.2 Python Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install core dependencies
pip install oracledb          # Oracle Database 23ai client
pip install pyodbc            # SQL Server (schema extraction only)
pip install requests          # Bitbucket API
pip install python-dotenv     # Environment variables
pip install pydantic          # Configuration validation
pip install tree-sitter       # Code parsing
pip install tree-sitter-c-sharp
pip install sqlparse          # SQL parsing
pip install numpy             # Vector operations
pip install fastapi uvicorn   # MCP server
pip install pyyaml            # Configuration
pip install jinja2            # Code templates
pip install langchain         # Optional: LLM orchestration
```

### 1.3 Directory Structure

```
migration-agent/
├── config/
│   ├── config.yaml              # Main configuration
│   ├── llm_cert.pem             # LLM server SSL certificate
│   └── .env                     # Secrets (not in git)
├── agent/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py          # Configuration loader
│   │   ├── llm_config.py        # LLM connection settings
│   │   ├── oracle_config.py     # Oracle DB settings
│   │   └── bitbucket_config.py  # Bitbucket settings
│   ├── core/
│   │   ├── parsers/
│   │   │   ├── __init__.py
│   │   │   ├── csharp_parser.py
│   │   │   ├── sql_parser.py
│   │   │   └── guideline_parser.py
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── oracle_manager.py
│   │   │   ├── vector_store.py
│   │   │   ├── graph_store.py
│   │   │   └── schema_store.py
│   │   ├── integrations/
│   │   │   ├── __init__.py
│   │   │   ├── bitbucket_client.py
│   │   │   └── llm_client.py
│   │   ├── generators/
│   │   │   ├── __init__.py
│   │   │   ├── java_generator.py
│   │   │   └── angular_generator.py
│   │   └── mcp/
│   │       ├── __init__.py
│   │       ├── server.py
│   │       └── resources.py
│   ├── orchestrator.py
│   └── main.py
├── sql/
│   ├── oracle_setup.sql         # Oracle schema creation
│   └── sqlserver_schema_extract.sql
├── tests/
│   ├── test_bitbucket.py
│   ├── test_oracle.py
│   └── test_llm.py
├── requirements.txt
└── README.md
```

**Code implemented in:**
- `agent/config/settings.py` - Configuration loader
- `agent/config/llm_config.py` - LLM configuration
- `agent/config/oracle_config.py` - Oracle configuration
- `agent/config/bitbucket_config.py` - Bitbucket configuration
- `agent/core/integrations/bitbucket_client.py` - Bitbucket API client
- `agent/core/integrations/llm_client.py` - LLM client
- `agent/core/storage/oracle_manager.py` - Oracle manager
- `agent/core/storage/vector_store.py` - Vector store
- `agent/core/storage/graph_store.py` - Graph store
- `agent/core/storage/schema_store.py` - Schema store
- `config/config.yaml` - Main configuration
- `config/.env.example` - Environment template
- `sql/oracle_setup.sql` - Oracle schema
- `sql/sqlserver_schema_extract.sql` - SQL Server queries

---

## 2. Configuration Files

### 2.1 Main Configuration (config/config.yaml)

```yaml
# Migration paths
migration:
  source:
    type: "bitbucket"
    workspace: "mycompany"
    repo_slug: "old-application"
    branch: "main"
    path_pattern: "src/**/*.cs"
    
  target:
    backend:
      path: "/path/to/new-app/backend"
      framework: "Spring Boot 3.2"
      package_base: "com.company.newapp"
    frontend:
      path: "/path/to/new-app/frontend"
      framework: "Angular 17"

# Oracle Database 23ai (unified storage)
oracle:
  host: "localhost"
  port: 1521
  service_name: "FREEPDB1"
  username: "migration_user"
  password: "${ORACLE_PASSWORD}"
  pool_size: 10
  
  vector:
    embedding_dimension: 1536
    distance_metric: "COSINE"
    
  graph:
    enabled: true

# SQL Server (existing database - schema extraction only)
sqlserver:
  host: "sqlserver.company.com"
  port: 1433
  database: "ProductionDB"
  username: "readonly_user"
  password: "${SQLSERVER_PASSWORD}"

# Bitbucket API
bitbucket:
  base_url: "https://api.bitbucket.org/2.0"
  token: "${BITBUCKET_TOKEN}"
  rate_limit_delay: 1.0

# Local LLM Server
llm:
  base_url: "https://llm-server.internal.company.com:8443"
  api_type: "openai"
  auth_type: "bearer"
  token: "${LLM_API_TOKEN}"
  verify_ssl: true
  cert_path: "config/llm_cert.pem"
  model_name: "llama-3-70b-instruct"
  max_tokens: 4000
  temperature: 0.2
  embedding_model: "text-embedding-ada-002"
  embedding_url: "https://llm-server.internal.company.com:8443/embeddings"

# MCP Server
mcp:
  server_name: "migration-context"
  host: "localhost"
  port: 8080

# Logging
logging:
  level: "INFO"
  file: "logs/migration.log"
```

### 2.2 Environment Variables (.env)

```bash
# Oracle Database
ORACLE_PASSWORD=your_oracle_password

# SQL Server (read-only)
SQLSERVER_PASSWORD=your_sqlserver_password

# Bitbucket
BITBUCKET_TOKEN=your_bitbucket_token

# LLM Server
LLM_API_TOKEN=your_llm_api_token
```

### 2.3 Oracle Setup SQL (sql/oracle_setup.sql)

```sql
-- Oracle 23ai Setup for Migration Agent
-- Run as ADMIN user

CREATE USER migration_user IDENTIFIED BY "SecurePassword123!";
GRANT CONNECT, RESOURCE TO migration_user;
GRANT UNLIMITED TABLESPACE TO migration_user;
GRANT CREATE PROPERTY GRAPH TO migration_user;

-- Vector Store Tables
CREATE TABLE code_vectors (
    id VARCHAR2(100) PRIMARY KEY,
    file_path VARCHAR2(1000) NOT NULL,
    component_type VARCHAR2(50) NOT NULL,
    component_name VARCHAR2(200) NOT NULL,
    namespace VARCHAR2(500),
    code_content CLOB NOT NULL,
    embedding VECTOR(1536, FLOAT32),
    metadata JSON,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE VECTOR INDEX code_vec_idx ON code_vectors(embedding)
ORGANIZATION NEIGHBOR PARTITIONS
DISTANCE COSINE;

-- Graph Tables
CREATE TABLE code_components (
    id VARCHAR2(100) PRIMARY KEY,
    name VARCHAR2(200) NOT NULL,
    type VARCHAR2(50) NOT NULL,
    namespace VARCHAR2(500),
    file_path VARCHAR2(1000),
    metadata JSON
);

CREATE TABLE code_dependencies (
    from_id VARCHAR2(100) NOT NULL,
    to_id VARCHAR2(100) NOT NULL,
    dependency_type VARCHAR2(50) NOT NULL,
    strength NUMBER(3, 2) DEFAULT 1.0,
    metadata JSON,
    PRIMARY KEY (from_id, to_id, dependency_type)
);

-- Transactional Tables
CREATE TABLE db_schema_reference (
    schema_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    schema_name VARCHAR2(200),
    table_name VARCHAR2(200) NOT NULL,
    column_definitions JSON NOT NULL,
    indexes JSON,
    relationships JSON
);

CREATE TABLE stored_procedures (
    proc_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    schema_name VARCHAR2(200),
    proc_name VARCHAR2(200) NOT NULL,
    parameters JSON,
    definition CLOB NOT NULL
);

CREATE TABLE coding_guidelines (
    guideline_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_type VARCHAR2(50) NOT NULL,
    guideline_content CLOB NOT NULL,
    architectural_patterns JSON
);

CREATE TABLE migration_logs (
    log_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    component_id VARCHAR2(100) NOT NULL,
    component_type VARCHAR2(50),
    migration_status VARCHAR2(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    error_message CLOB,
    generated_code CLOB
);

COMMIT;
```

---

## 3. Core Implementation

**Code implemented in:**
- `agent/config/settings.py` - Full configuration loader
- `agent/core/integrations/bitbucket_client.py` - Bitbucket client with tree fetching and file filtering
- `agent/core/integrations/llm_client.py` - LLM client with embeddings and completions
- `agent/orchestrator.py` - Main migration workflow orchestrator
- `agent/core/generators/java_generator.py` - Spring Boot code generation
- `agent/core/generators/angular_generator.py` - Angular component generation

---

## 4. Oracle Database Manager

**Code implemented in:**
- `agent/core/storage/oracle_manager.py` - Connection pooling and query execution
- `agent/core/storage/vector_store.py` - Vector search for code similarity
- `agent/core/storage/graph_store.py` - Dependency graph management
- `agent/core/storage/schema_store.py` - SQL Server schema reference storage

---

## 5. MCP Server

**Code implemented in:**
- `agent/core/mcp/server.py` - MCP server with resource handlers
- `agent/core/mcp/resources.py` - Migration context templates

---

## 6. Usage Examples

### 6.1 Basic Usage

```bash
# 1. Set up environment
cp config/.env.example config/.env
# Edit .env with your credentials

# 2. Test connections
python agent/main.py --test-connection

# 3. Run full migration
python agent/main.py

# 4. Migrate specific component
python agent/main.py --component UserController.cs

# 5. Migrate only controllers
python agent/main.py --type controller
```

### 6.2 Custom LLM Configuration Examples

**llama.cpp server:**
```yaml
llm:
  base_url: "https://llm.internal:8443"
  api_type: "openai"
  auth_type: "bearer"
  model_name: "llama-3-70b-instruct"
```

**vLLM server:**
```yaml
llm:
  base_url: "http://vllm-server:8000"
  api_type: "openai"
  auth_type: "api_key"
  model_name: "mistralai/Mistral-7B-Instruct-v0.2"
```

---

## 7. Monitoring & Debugging

### 7.1 Query Migration Progress

```sql
-- Check migration progress
SELECT * FROM v_migration_progress;

-- View failed migrations
SELECT component_id, component_type, error_message
FROM migration_logs
WHERE migration_status = 'FAILED';
```

### 7.2 Debug Logging

```yaml
logging:
  level: "DEBUG"
  file: "logs/migration.log"
```

---

This completes the implementation guide for Oracle + Bitbucket + Local LLM configuration!
