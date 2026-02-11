SELECT 
    t.TABLE_SCHEMA,
    t.TABLE_NAME,
    c.COLUMN_NAME,
    c.DATA_TYPE,
    c.IS_NULLABLE,
    c.CHARACTER_MAXIMUM_LENGTH,
    c.NUMERIC_PRECISION,
    c.NUMERIC_SCALE
FROM INFORMATION_SCHEMA.TABLES t
JOIN INFORMATION_SCHEMA.COLUMNS c 
    ON t.TABLE_NAME = c.TABLE_NAME AND t.TABLE_SCHEMA = c.TABLE_SCHEMA
WHERE t.TABLE_TYPE = 'BASE TABLE'
ORDER BY t.TABLE_NAME, c.ORDINAL_POSITION;

SELECT 
    i.name AS index_name,
    i.type_desc AS index_type,
    i.is_unique,
    i.is_primary_key,
    COL_NAME(ic.object_id, ic.column_id) AS column_name,
    ic.key_ordinal
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
WHERE i.object_id = OBJECT_ID('dbo.TableName')
ORDER BY i.name, ic.key_ordinal;

SELECT 
    ROUTINE_SCHEMA,
    ROUTINE_NAME,
    ROUTINE_DEFINITION,
    DATA_TYPE AS return_type,
    CHARACTER_MAXIMUM_LENGTH AS max_length
FROM INFORMATION_SCHEMA.ROUTINES
WHERE ROUTINE_TYPE = 'PROCEDURE';

SELECT 
    PARAMETER_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    PARAMETER_MODE,
    ORDINAL_POSITION
FROM INFORMATION_SCHEMA.PARAMETERS
WHERE SPECIFIC_NAME = 'ProcedureName'
ORDER BY ORDINAL_POSITION;

SELECT 
    FK.name AS fk_name,
    OBJECT_NAME(FK.parent_object_id) AS table_name,
    COL_NAME(FKC.parent_object_id, FKC.parent_column_id) AS column_name,
    OBJECT_NAME(FKC.referenced_object_id) AS referenced_table,
    COL_NAME(FKC.referenced_object_id, FKC.referenced_column_id) AS referenced_column
FROM sys.foreign_keys FK
JOIN sys.foreign_key_columns FKC ON FK.object_id = FKC.constraint_object_id;
