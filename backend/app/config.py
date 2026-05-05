from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./meetingcost.db"
    SECRET_KEY: str = "dev-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    TEAMS_APP_ID: str = ""
    TEAMS_CLIENT_SECRET: str = ""
    AZURE_TENANT_ID: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
