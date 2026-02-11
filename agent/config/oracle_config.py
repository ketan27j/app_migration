from pydantic import BaseModel

class OracleConfig(BaseModel):
    host: str
    port: int
    service_name: str
    username: str
    password: str
    pool_size: int = 10
    vector_embedding_dimension: int = 1536
    vector_distance_metric: str = "COSINE"
