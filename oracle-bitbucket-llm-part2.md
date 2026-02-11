# Migration Agent Implementation - Part 2
## Graph Store, Orchestrator, and Main Execution

---

## 5. Graph Store

**Code implemented in:** `agent/core/storage/graph_store.py`

### Features:
- Component node creation and management
- Dependency edge creation
- Dependency traversal (direct and recursive)
- Circular dependency detection

---

## 6. Schema Store

**Code implemented in:** `agent/core/storage/schema_store.py`

### Features:
- SQL Server table schema storage
- Stored procedure reference storage
- Table search by keyword
- Schema retrieval for migration context

---

## 7. Migration Orchestrator

**Code implemented in:** `agent/orchestrator.py`

### Migration Workflow:

1. **Fetch old code from Bitbucket**
   - Get repository tree
   - Filter by path pattern
   - Fetch file contents

2. **Parse and store in Oracle**
   - Parse C# files
   - Generate embeddings
   - Store in vector and graph stores

3. **Extract SQL Server schema (context only)**
   - Get table definitions
   - Get stored procedures
   - Store as reference (no migration)

4. **Parse coding guidelines**
   - Read README.md files
   - Extract guidelines
   - Store for LLM context

5. **Migrate components**
   - Controllers → Spring Boot controllers
   - Services → Spring services
   - Models → JPA entities
   - Views → Angular components

6. **Generate summary report**
   - Migration statistics
   - Failed migrations
   - Success rates

---

## 8. Main Execution

**Code implemented in:** `agent/main.py`

### Command Line Options:

```bash
python agent/main.py --test-connection  # Test all connections
python agent/main.py                     # Run full migration
python agent/main.py --component X       # Migrate specific component
python agent/main.py --type controller   # Migrate by type
```

### Connection Tests:
- Bitbucket API
- Oracle Database
- LLM Server
- SQL Server

---

## 9. Generators

### Java Generator

**Code implemented in:** `agent/core/generators/java_generator.py`

Generates:
- Spring Boot REST Controllers
- DTOs
- Services
- Repositories

### Angular Generator

**Code implemented in:** `agent/core/generators/angular_generator.py`

Generates:
- Components (TypeScript)
- Services
- Models/Interfaces
- HTML templates

---

## 10. MCP Server

**Code implemented in:** 
- `agent/core/mcp/server.py` - Server implementation
- `agent/core/mcp/resources.py` - Context templates

### Resources:
- `code://old-app/controllers` - ASP.NET Controllers
- `docs://functional-specs` - Functional Documentation
- `schema://database` - Database Schema

---

## 11. Configuration Summary

### Files Created:

```
config/
├── config.yaml              # Main configuration
├── .env.example             # Environment template

agent/
├── config/
│   ├── settings.py          # Configuration loader
│   ├── llm_config.py        # LLM settings
│   ├── oracle_config.py     # Oracle settings
│   └── bitbucket_config.py  # Bitbucket settings
├── core/
│   ├── parsers/
│   │   ├── csharp_parser.py
│   │   ├── sql_parser.py
│   │   └── guideline_parser.py
│   ├── storage/
│   │   ├── oracle_manager.py
│   │   ├── vector_store.py
│   │   ├── graph_store.py
│   │   └── schema_store.py
│   ├── integrations/
│   │   ├── bitbucket_client.py
│   │   └── llm_client.py
│   ├── generators/
│   │   ├── java_generator.py
│   │   └── angular_generator.py
│   └── mcp/
│       ├── server.py
│       └── resources.py
├── orchestrator.py
└── main.py

sql/
├── oracle_setup.sql
└── sqlserver_schema_extract.sql
```

---

## 12. Quick Start

### 1. Configure Environment

```bash
cp config/.env.example config/.env
# Edit config/.env with your credentials
```

### 2. Setup Oracle Database

```bash
# Run oracle_setup.sql in SQL*Plus or SQLcl
sql> @sql/oracle_setup.sql
```

### 3. Test Connections

```bash
python agent/main.py --test-connection
```

### 4. Run Migration

```bash
python agent/main.py
```

---

## 13. Migration Progress Tracking

### Views Created:

- `v_migration_progress` - Component migration status summary
- `v_component_dependencies` - Component dependency graph

### Tables:

- `migration_logs` - All migration attempts with status
- `file_mappings` - Old to new file path mappings

---

This completes Part 2 of the migration agent implementation!
