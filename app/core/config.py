"""Configuration settings for the RetroLens backend."""

import json
import sys
from typing import List, Union, Optional
from pydantic import field_validator, ConfigDict, ValidationError
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "RetroLens"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_PROJECT_ID: str
    
    # Security
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = []
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Clerk Configuration
    CLERK_DOMAIN: Optional[str] = None
    CLERK_SECRET_KEY: Optional[str] = None
    CLERK_AUDIENCE: Optional[str] = None
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str):
            if v.startswith("["):
                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(v)
    
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )


try:
    settings = Settings()
except ValidationError as e:
    print("\n" + "="*50)
    print("CONFIGURATION ERROR")
    print("="*50)
    print("\nMissing or invalid environment variables:")
    for error in e.errors():
        field = error['loc'][0] if error['loc'] else 'unknown'
        print(f"  - {field}: {error['msg']}")
    print("\nPlease set the required environment variables in Railway.")
    print("\nRequired variables:")
    print("  - SUPABASE_URL")
    print("  - SUPABASE_ANON_KEY")
    print("  - SUPABASE_SERVICE_KEY")
    print("  - SUPABASE_PROJECT_ID")
    print("  - SECRET_KEY (generate a secure key!)")
    print("  - BACKEND_CORS_ORIGINS")
    print("\n" + "="*50 + "\n")
    sys.exit(1)
