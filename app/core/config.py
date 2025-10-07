from pydantic import BaseSettings
class Settings(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    REDIS_URL: str
    ES_HOST: str
    QWEN_API_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = 'HS256'

    class Config:
        env_file = '../../.env'

settings = Settings()