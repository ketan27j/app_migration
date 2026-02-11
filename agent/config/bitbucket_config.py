from pydantic import BaseModel

class BitbucketConfig(BaseModel):
    base_url: str = "https://api.bitbucket.org/2.0"
    token: str
    rate_limit_delay: float = 1.0
