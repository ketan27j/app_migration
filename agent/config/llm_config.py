from pydantic import BaseModel
from typing import Dict, Optional

class LLMConfig(BaseModel):
    base_url: str
    api_type: str = "openai"
    auth_type: str = "bearer"
    token: str
    verify_ssl: bool = True
    cert_path: Optional[str] = None
    model_name: str
    max_tokens: int = 4000
    temperature: float = 0.2
    embedding_model: str
    embedding_url: Optional[str] = None
    custom_headers: Dict[str, str] = {}
