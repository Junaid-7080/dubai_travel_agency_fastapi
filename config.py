from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Use SQLite for development by default
    # To use PostgreSQL, set DATABASE_URL environment variable to: postgresql://postgres:password@localhost:5432/dubai_travel
    database_url: str = "postgresql://dubai_traval_agency:12345@host:5432/dubai_travel_db"
    secret_key: str = "dubai_travel_agency"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Payment settings (optional for testing)
    stripe_secret_key: str = "sk_test_dummy_key"
    stripe_publishable_key: str = "pk_test_dummy_key"
    paypal_client_id: str = "dummy_paypal_client_id"
    paypal_client_secret: str = "dummy_paypal_secret"
    paytabs_merchant_id: str = "dummy_paytabs_merchant"
    paytabs_secret_key: str = "dummy_paytabs_secret"
    
    # Communication settings (optional for testing)
    twilio_account_sid: str = "dummy_twilio_sid"
    twilio_auth_token: str = "dummy_twilio_token"
    twilio_phone_number: str = "+1234567890"
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = "dummy@gmail.com"
    smtp_password: str = "dummy_password"
    
    # Other settings
    redis_url: str = "redis://localhost:6379"
    upload_dir: str = "uploads"
    max_file_size: int = 10485760
    
    class Config:
        env_file = ".env"

settings = Settings()