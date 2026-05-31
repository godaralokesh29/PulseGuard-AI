"""Configuration management for RAG of Fire backend."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    app_name: str = "PulseGuard-AI"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost/rag_of_fire"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    
    # Security
    jwt_secret: str = "super_secret_jwt_key_change_in_production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # Observability
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    
    # Vector DB
    vector_db_path: str = "./data/chroma_db"
    embedding_model: str = "gemini-embedding-001"
    
    # LLM
    use_real_llm: bool = True
    llm_provider: str = "gemini"  # gemini, openai, anthropic
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    llm_model: str = "gemini-3.5-flash"
    
    # Notifications
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    slack_webhook_url: str = ""
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
