from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720
    
    # Acceso para admin
    SECRET_KEY_JWT_ADMIN: str
    COOKIE_NAME_ADMIN: str = "access_token"

    # Acceso para superadmin
    SECRET_KEY_JWT_SA: str
    COOKIE_NAME_SA: str = "sa_access_token"

    # Accesos para recuperacion de contraseña por GMAIL.
    SMTP_HOST: str
    SMTP_PORT: int = 465
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_NAME: str = "RMOSOFT"
    SA_RESET_EXPIRE_MINUTES: int = 15
    FRONTEND_BASE_URL: str = "http://127.0.0.1:8000"
    

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    #class Config:
    #    env_file = ".env"

settings = Settings()