import requests
import json
from typing import List, Dict, Optional, Union
import ssl
import certifi

class LocalLLMClient:
    def __init__(self, config):
        self.base_url = config.base_url.rstrip('/')
        self.api_type = config.api_type
        self.auth_type = config.auth_type
        self.token = config.token
        self.model_name = config.model_name
        self.embedding_model = config.embedding_model
        self.embedding_url = config.embedding_url or f"{self.base_url}/embeddings"
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature
        self.verify_ssl = config.verify_ssl
        self.cert_path = config.cert_path
        self.custom_headers = config.custom_headers or {}
        self.session = requests.Session()
        self._setup_authentication()
        self._setup_ssl()
    
    def _setup_authentication(self):
        headers = {'Content-Type': 'application/json'}
        if self.auth_type == 'bearer':
            headers['Authorization'] = f'Bearer {self.token}'
        elif self.auth_type == 'api_key':
            headers['api-key'] = self.token
        headers.update(self.custom_headers)
        self.session.headers.update(headers)
    
    def _setup_ssl(self):
        if not self.verify_ssl:
            self.session.verify = False
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        elif self.cert_path:
            self.session.verify = self.cert_path
        else:
            self.session.verify = certifi.where()
    
    def generate_completion(
        self, prompt: str, system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None, temperature: Optional[float] = None,
        stream: bool = False
    ) -> Union[str, Dict]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": max_tokens or self.max_tokens,
            "temperature": temperature or self.temperature,
            "stream": stream
        }
        
        try:
            url = f"{self.base_url}/chat/completions"
            response = self.session.post(url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            return result
        except requests.exceptions.RequestException as e:
            print(f"LLM API Error: {e}")
            if hasattr(e.response, 'text'):
                print(f"Response: {e.response.text}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        payload = {"model": self.embedding_model, "input": text}
        try:
            response = self.session.post(self.embedding_url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            if 'data' in result and len(result['data']) > 0:
                return result['data'][0]['embedding']
            raise ValueError("No embedding in response")
        except requests.exceptions.RequestException as e:
            print(f"Embedding API Error: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        payload = {"model": self.embedding_model, "input": texts}
        try:
            response = self.session.post(self.embedding_url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            if 'data' in result:
                return [item['embedding'] for item in result['data']]
            raise ValueError("No embeddings in response")
        except requests.exceptions.RequestException as e:
            print(f"Batch Embedding API Error: {e}")
            raise
    
    def test_connection(self) -> bool:
        try:
            response = self.generate_completion(prompt="Hello, this is a test.", max_tokens=10)
            print(f"Connection successful. Response: {response[:100]}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

if __name__ == "__main__":
    from agent.config.settings import settings
    
    client = LocalLLMClient(settings.llm)
    
    if client.test_connection():
        print("✓ LLM connection successful")
        embedding = client.generate_embedding("Test code snippet")
        print(f"✓ Embedding generated: dimension={len(embedding)}")
    else:
        print("✗ LLM connection failed")
