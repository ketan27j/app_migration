# Application Migration Agent: ASP.NET to Java/Angular
## Comprehensive Implementation Plan (Oracle + Bitbucket + Local LLM)

---

## Executive Summary

This document outlines a detailed plan for developing an AI-powered migration agent that transforms ASP.NET/C#/SQL Server applications into modern Java/Angular stack applications. The agent uses Oracle Database 23ai for unified storage (transactional, vector, and graph), connects to Bitbucket for code access, leverages a local LLM server, and preserves existing SQL Server stored procedures without migration.

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Migration Agent System                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────┐      ┌──────────────────┐              │
│  │  Bitbucket     │──────│  Code Fetcher    │              │
│  │  Integration   │      │  (Token Auth)    │              │
│  └────────────────┘      └──────────────────┘              │
│                                                               │
│  ┌────────────────┐      ┌──────────────────┐              │
│  │  Code Parser   │──────│  Oracle DB 23ai  │              │
│  │  & Analyzer    │      │  - Vector Store  │              │
│  │                │      │  - Graph Store   │              │
│  └────────────────┘      │  - Metadata      │              │
│                          └──────────────────┘              │
│                                                               │
│  ┌────────────────┐      ┌──────────────────┐              │
│  │  Guidelines    │──────│  MCP Server      │              │
│  │  Parser        │      │  (Context)       │              │
│  │  (README.md)   │      │  - Code Context  │              │
│  └────────────────┘      │  - Guidelines    │              │
│                          │  - DB Schema     │              │
│                          └──────────────────┘              │
│                                                               │
│  ┌────────────────────────────────────────────┐             │
│  │       Local LLM Engine (Custom Config)     │             │
│  │  - HTTPS with Certificate                  │             │
│  │  - Custom Headers/Auth                     │             │
│  │  - Code Translation                       │             │
│  │  - Guideline Enforcement                  │             │
│  └────────────────────────────────────────────┘             │
│                                                               │
│  ┌──────────────┐              ┌──────────────┐             │
│  │  Backend     │              │  Frontend    │             │
│  │  Generator   │              │  Generator   │             │
│  │  (Java)      │              │  (Angular)   │             │
│  └──────────────┘              └──────────────┘             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐          ┌─────────────────┐
│  Old System     │          │  New System     │
│  (ASP.NET)      │          │  (Java/Angular)│
│  + SQL Server   │          │  + SQL Server   │
│  Running: 8080  │          │  (Same DB)      │
│                 │          │  Running: 3000  │
└─────────────────┘          └─────────────────┘
         │                              │
         └──────────────┬───────────────┘
                        ▼
                ┌──────────────┐
                │  SQL Server  │
                │  (Shared DB) │
                │  + SPs        │
                └──────────────┘
```

### 1.2 Key Architectural Decisions

**Oracle Database 23ai as Unified Store:**
- **Vector Store**: Oracle AI Vector Search for code embeddings
- **Graph Store**: Oracle Property Graph for dependency tracking
- **Transactional**: Metadata, migration logs, mappings
- **Schema Context**: SQL Server schema stored as reference (read-only)

**No Database Migration:**
- SQL Server database remains unchanged
- Stored Procedures used as-is in new Java application
- Only database schema captured for context
- Both old and new apps connect to same SQL Server

**Bitbucket Integration:**
- read_file old code via Bitbucket API with token authentication
- write_to_file new code to specified output directory
- No commits to Bitbucket by agent (manual review required)

**Local LLM Server:**
- Custom HTTPS configuration with certificate validation
- Configurable endpoint, headers, and authentication
- Support for various LLM formats (OpenAI-compatible API)

**Guideline-Driven Generation:**
- Parse README.md for coding guidelines
- Extract architectural patterns from new project structure
- Enforce guidelines in every code generation request

---

## 2. Technology Stack

### 2.1 Migration Agent Core

**Python-based Agent (Recommended)**
- **Framework**: LangChain for orchestration
- **Database**: Oracle Database 23ai (unified store)
- **Bitbucket Client**: `requests` library with token auth
- **MCP Server**: Custom MCP server using FastMCP or mcp-python
- **LLM Client**: Custom configurable client with HTTPS/certificate support
- **Code Parsing**: Tree-sitter, Roslyn (C#), JavaParser (Java)
- **SQL Parsing**: sqlparse for SQL Server schema extraction

### 2.2 Oracle Database 23ai Configuration

**Unified Storage Approach:**

1. **Vector Search (AI Vector Search)**
   - Code embeddings storage

2. **Property Graph (Native Graph)**
   - Component relationships

3. **Transactional Tables**
   - Migration metadata
   - SQL Server schema reference (read-only context)
   - Coding guidelines cache

### 2.3 Bitbucket Integration

**API Access Configuration:**
- Authentication: Personal Access Token or App Password
- API Version: Bitbucket REST API 2.0
- Required Permissions: Repository read
- Rate Limiting: Implemented with backoff

### 2.4 Local LLM Configuration

**Flexible LLM Client Supporting:**
- OpenAI-compatible API endpoints
- Custom HTTPS with certificate validation
- Bearer token authentication
- Custom headers for API keys
- Configurable model parameters
- Streaming responses (optional)

**Supported LLM Formats:**
- LLaMA/LLaMA2 via llama.cpp server
- Mistral via vLLM
- Custom fine-tuned models
- Any OpenAI API-compatible endpoint

---

## 3. Detailed Implementation Plan

### Phase 1: Setup & Analysis (Weeks 1-2)

#### 3.1 Repository Structure

```
migration-agent/
├── agent/
│   ├── core/
│   │   ├── parsers/
│   │   │   ├── csharp_parser.py
│   │   │   ├── sql_parser.py
│   │   │   └── guideline_parser.py
│   │   ├── storage/
│   │   │   ├── oracle_manager.py
│   │   │   ├── vector_store.py
│   │   │   ├── graph_store.py
│   │   │   └── schema_store.py
│   │   ├── integrations/
│   │   │   ├── bitbucket_client.py
│   │   │   └── llm_client.py
│   │   ├── mcp/
│   │   │   ├── server.py
│   │   │   └── resources.py
│   │   └── generators/
│   │       ├── java_generator.py
│   │       └── angular_generator.py
│   ├── config/
│   │   ├── llm_config.py
│   │   ├── oracle_config.py
│   │   └── bitbucket_config.py
│   ├── orchestrator.py
│   └── main.py
├── config/
│   ├── config.yaml
│   ├── llm_cert.pem
│   └── guidelines/
├── sql/
│   ├── oracle_setup.sql
│   └── schema_extraction.sql
├── tests/
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

**Code for:**
- `agent/config/settings.py` - Configuration loader
- `agent/core/integrations/bitbucket_client.py` - Bitbucket API client
- `agent/core/integrations/llm_client.py` - Configurable LLM client
- `agent/core/storage/oracle_manager.py` - Unified Oracle DB manager
- `agent/core/storage/vector_store.py` - Oracle AI Vector Search
- `agent/core/storage/graph_store.py` - Oracle Property Graph
- `agent/core/storage/schema_store.py` - SQL Server schema reference

#### 3.2 Code Fetching & Analysis with Bitbucket

**Step 1: Fetch Code from Bitbucket**
- Get repository content
- Filter based on path pattern
- Download relevant files

**Step 2: Extract SQL Server Schema (Context Only)**
- Get table schemas
- Get stored procedures
- Store in Oracle vector store for semantic search

**Step 3: Parse Coding Guidelines**
- read_file backend/frontend README.md
- Extract architectural patterns from project structure
- Store in Oracle for LLM context

### Phase 2: MCP Server Setup (Week 3)

#### 3.3 MCP Server Configuration

**Resources:**
- `code://old-app/controllers` - ASP.NET Controllers
- `docs://functional-specs` - Functional Documentation
- `schema://database` - Database Schema

**Implementation:**
- Query vector DB for relevant code
- Get related dependencies from graph
- Combine context for LLM

### Phase 3: Migration Engine (Weeks 4-6)

#### 3.4 AI-Powered Code Translation

**Component-by-Component Migration:**
1. Migrate Database Schema
2. Migrate Models/Entities
3. Migrate Data Access Layer
4. Migrate Business Logic
5. Migrate API Controllers
6. Migrate Frontend

**Migration Prompts:**
- CONTROLLER_MIGRATION_PROMPT
- FRONTEND_MIGRATION_PROMPT

### Phase 4: Testing & Validation (Weeks 7-8)

#### 3.6 Dual System Deployment

**Docker Compose Configuration:**
- Old ASP.NET Application (port 8080)
- SQL Server
- New Java Backend (port 8081)
- PostgreSQL
- New Angular Frontend (port 4200)
- Migration Agent
- ChromaDB

#### 3.7 Validation Strategy

- API Contract Testing
- Database Schema Validation
- Business Logic Validation
- Performance Testing

---

## 4. Detailed Workflow

### 4.1 Step-by-Step Migration Process

**Week 1-2: Preparation**
- Set up vector database
- Parse entire ASP.NET codebase
- Generate code embeddings
- Build dependency graph
- Parse functional documentation
- Set up MCP server

**Week 3: Database Migration**
- Extract SQL Server schema
- Generate PostgreSQL migration scripts
- Convert stored procedures to JPA queries
- Migrate reference data
- Validate data integrity

**Week 4: Backend Migration**
- Generate JPA entities from C# models
- Convert repositories to Spring Data JPA
- Migrate service layer business logic
- Convert controllers to REST endpoints
- Implement security

**Week 5: Frontend Migration**
- Create Angular project structure
- Generate components from views
- Implement services for API calls
- Convert forms and validation
- Implement routing

**Week 6: Integration**
- Connect frontend to backend
- Test end-to-end workflows
- Fix integration issues
- Optimize performance

**Week 7-8: Testing & Refinement**
- Parallel testing
- Fix discrepancies
- Performance optimization
- Documentation

---

## 5. Best Practices & Recommendations

### 5.1 Memory Management Strategy

**Chunking Strategy:**
- Store code at file level
- Create embeddings for classes/methods
- Link related code through graph database
- Maintain metadata (file path, line numbers, dependencies)

**Retrieval Strategy:**
- Vector search for similar code
- Get direct dependencies
- Get functional documentation
- Combine context

### 5.2 MCP Server Best Practices

**Resource Organization:**
```
mcp://migration-context/
├── code/
├── docs/
├── schema/
└── mappings/
```

### 5.3 Incremental Migration Approach

**Recommended Migration Order:**
1. Database Schema
2. Models/Entities
3. Data Access Layer
4. Business Logic
5. API Layer
6. Frontend Components
7. Integration & Testing

---

## 6. Technology-Specific Mappings

### 6.1 ASP.NET to Spring Boot Mapping

| ASP.NET | Spring Boot |
|---------|-------------|
| Controller | @RestController |
| [HttpGet] | @GetMapping |
| [HttpPost] | @PostMapping |
| IActionResult | ResponseEntity<T> |
| DbContext | JpaRepository |
| Entity Framework | Spring Data JPA |
| appsettings.json | application.yml |
| Dependency Injection | @Autowired |

### 6.2 Razor/MVC to Angular Mapping

| ASP.NET MVC | Angular |
|-------------|---------|
| View | Component Template |
| ViewModel | Component Class |
| Model Binding | Reactive Forms |
| Html.ActionLink | routerLink |
| Ajax.BeginForm | HttpClient + RxJS |
| Partial Views | Child Components |
| Layout | App Component |

---

## 7. Monitoring & Logging

### 7.1 Migration Dashboard

Create a real-time dashboard showing:
- Components migrated vs pending
- Test coverage comparison
- Performance metrics
- API contract compatibility
- Database migration status

### 7.2 Logging Strategy

Use Python logging with:
- Migration start/end logging
- Success/failure metrics
- Error tracking

---

## 8. Risk Mitigation

### 8.1 Common Challenges & Solutions

**Challenge 1: Business Logic Loss**
- Solution: Extensive functional documentation in MCP
- Validation: Parallel testing with identical inputs

**Challenge 2: Database Schema Differences**
- Solution: Create mapping tables, use migration scripts
- Validation: Data integrity checks

**Challenge 3: Performance Degradation**
- Solution: Benchmark both systems, optimize queries
- Validation: Load testing comparison

**Challenge 4: Security Gaps**
- Solution: Security review checklist, automated scanning
- Validation: Penetration testing

---

## 9. Success Metrics

### 9.1 KPIs to Track

1. **Code Quality**
   - Test coverage (aim for 80%+)
   - Code complexity (lower is better)
   - Technical debt ratio

2. **Functional Parity**
   - API endpoint coverage (100%)
   - Feature completeness (100%)
   - Business rule accuracy (100%)

3. **Performance**
   - Response time comparison
   - Throughput comparison
   - Resource utilization

4. **Development Velocity**
   - Time per component migration
   - AI-generated vs manual code ratio
   - Bug fix rate

---

## 10. Next Steps

### Immediate Actions:
1. Choose vector database (recommend ChromaDB for POC)
2. Set up development environment
3. Clone old application repository
4. Install MCP SDK and dependencies
5. Create initial parsers for C# code

### First Sprint Goals:
- Parse 1 controller completely
- Store in vector DB
- Set up basic MCP server
- Generate 1 Spring Boot controller
- Validate output

---

## Appendix A: Tool Recommendations

### A.1 Code Analysis Tools
- **Roslyn**: C# code analysis
- **NRefactory**: ASP.NET parsing
- **JavaParser**: Java code generation
- **ts-morph**: TypeScript manipulation

### A.2 Vector Databases Comparison

| Database | Pros | Cons | Best For |
|----------|------|------|----------|
| ChromaDB | Easy setup, local | Limited scale | POC, Development |
| Pinecone | Managed, scalable | Cost | Production |
| Weaviate | Feature-rich, OSS | Setup complexity | Self-hosted production |

### A.3 MCP Server Options
- **FastMCP** (Python): Fastest setup
- **mcp-python**: Official SDK
- **@modelcontextprotocol/sdk** (Node.js): For TS/JS projects

---

## Appendix B: Sample Code Snippets

### B.1 Vector Store Implementation

See `agent/core/storage/vector_store.py`

### B.2 Graph Database Schema

See `agent/core/storage/graph_store.py`

---

## Conclusion

This migration agent approach combines AI-powered code generation with structured knowledge management through vector databases and MCP servers. The key to success is:

1. **Comprehensive Context**: Store all old code, documentation, and schemas
2. **Structured Approach**: Migrate layer by layer
3. **Continuous Validation**: Keep both systems running for comparison
4. **Incremental Delivery**: Migrate and test one component at a time

The estimated timeline is 8-10 weeks for a medium-sized application, with the agent becoming more efficient as it learns patterns from successful migrations.
