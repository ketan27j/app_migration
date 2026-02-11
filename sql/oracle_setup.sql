CREATE USER migration_user IDENTIFIED BY "SecurePassword123!";
GRANT CONNECT, RESOURCE TO migration_user;
GRANT UNLIMITED TABLESPACE TO migration_user;
GRANT CREATE PROPERTY GRAPH TO migration_user;

CREATE TABLE code_vectors (
    id VARCHAR2(100) PRIMARY KEY,
    file_path VARCHAR2(1000) NOT NULL,
    component_type VARCHAR2(50) NOT NULL,
    component_name VARCHAR2(200) NOT NULL,
    namespace VARCHAR2(500),
    code_content CLOB NOT NULL,
    embedding VECTOR(1536, FLOAT32),
    metadata JSON,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    updated_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE VECTOR INDEX code_vec_idx ON code_vectors(embedding)
ORGANIZATION NEIGHBOR PARTITIONS
DISTANCE COSINE
WITH TARGET ACCURACY 95;

CREATE TABLE schema_vectors (
    id VARCHAR2(100) PRIMARY KEY,
    table_name VARCHAR2(200) NOT NULL,
    schema_text CLOB NOT NULL,
    embedding VECTOR(1536, FLOAT32),
    metadata JSON,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE VECTOR INDEX schema_vec_idx ON schema_vectors(embedding)
ORGANIZATION NEIGHBOR PARTITIONS
DISTANCE COSINE
WITH TARGET ACCURACY 95;

CREATE TABLE code_components (
    id VARCHAR2(100) PRIMARY KEY,
    name VARCHAR2(200) NOT NULL,
    type VARCHAR2(50) NOT NULL,
    namespace VARCHAR2(500),
    file_path VARCHAR2(1000),
    metadata JSON,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE TABLE code_dependencies (
    from_id VARCHAR2(100) NOT NULL,
    to_id VARCHAR2(100) NOT NULL,
    dependency_type VARCHAR2(50) NOT NULL,
    strength NUMBER(3, 2) DEFAULT 1.0,
    metadata JSON,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    PRIMARY KEY (from_id, to_id, dependency_type),
    FOREIGN KEY (from_id) REFERENCES code_components(id) ON DELETE CASCADE,
    FOREIGN KEY (to_id) REFERENCES code_components(id) ON DELETE CASCADE
);

CREATE PROPERTY GRAPH code_dependency_graph
    VERTEX TABLES (
        code_components KEY (id)
        LABEL component
        PROPERTIES (id, name, type, namespace, file_path, metadata)
    )
    EDGE TABLES (
        code_dependencies
        KEY (from_id, to_id, dependency_type)
        SOURCE KEY (from_id) REFERENCES code_components(id)
        DESTINATION KEY (to_id) REFERENCES code_components(id)
        LABEL depends_on
        PROPERTIES (dependency_type, strength, metadata)
    );

CREATE TABLE db_schema_reference (
    schema_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    schema_name VARCHAR2(200),
    table_name VARCHAR2(200) NOT NULL,
    column_definitions JSON NOT NULL,
    indexes JSON,
    relationships JSON,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    UNIQUE (schema_name, table_name)
);

CREATE TABLE stored_procedures (
    proc_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    schema_name VARCHAR2(200),
    proc_name VARCHAR2(200) NOT NULL,
    parameters JSON,
    definition CLOB NOT NULL,
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP,
    UNIQUE (schema_name, proc_name)
);

CREATE TABLE coding_guidelines (
    guideline_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    project_type VARCHAR2(50) NOT NULL,
    guideline_content CLOB NOT NULL,
    architectural_patterns JSON,
    last_updated TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE TABLE migration_logs (
    log_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    component_id VARCHAR2(100) NOT NULL,
    component_type VARCHAR2(50),
    migration_status VARCHAR2(50) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    error_message CLOB,
    generated_code CLOB,
    output_path VARCHAR2(1000),
    FOREIGN KEY (component_id) REFERENCES code_components(id)
);

CREATE TABLE file_mappings (
    mapping_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    old_file_path VARCHAR2(1000) NOT NULL,
    new_file_path VARCHAR2(1000) NOT NULL,
    component_type VARCHAR2(50),
    migration_status VARCHAR2(50),
    created_at TIMESTAMP DEFAULT SYSTIMESTAMP
);

CREATE INDEX idx_code_vectors_type ON code_vectors(component_type);
CREATE INDEX idx_code_vectors_name ON code_vectors(component_name);
CREATE INDEX idx_components_type ON code_components(type);
CREATE INDEX idx_migration_logs_status ON migration_logs(migration_status);
CREATE INDEX idx_migration_logs_component ON migration_logs(component_id);

CREATE OR REPLACE VIEW v_migration_progress AS
SELECT component_type, migration_status, COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY component_type), 2) as percentage
FROM migration_logs
GROUP BY component_type, migration_status;

CREATE OR REPLACE VIEW v_component_dependencies AS
SELECT c1.name as component_name, c1.type as component_type, c2.name as depends_on,
    c2.type as dependency_type, d.strength
FROM code_components c1
JOIN code_dependencies d ON c1.id = d.from_id
JOIN code_components c2 ON d.to_id = c2.id;

COMMIT;
