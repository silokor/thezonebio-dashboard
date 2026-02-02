"""
E-Commerce Dashboard Configuration
Fill in your API credentials for each platform.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Cafe24Config(BaseSettings):
    """Cafe24 API Configuration"""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    mall_id: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    api_base_url: str = "https://api.cafe24.com/api/v2"
    
    class Config:
        env_prefix = "CAFE24_"


class NaverConfig(BaseSettings):
    """Naver SmartStore API Configuration"""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    access_token: Optional[str] = None
    api_base_url: str = "https://api.commerce.naver.com/external/v1"
    
    class Config:
        env_prefix = "NAVER_"


class CoupangConfig(BaseSettings):
    """Coupang Wing API Configuration"""
    vendor_id: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    api_base_url: str = "https://api-gateway.coupang.com/v2/providers/openapi/apis"
    
    class Config:
        env_prefix = "COUPANG_"


class AppConfig(BaseSettings):
    """Main Application Configuration"""
    app_name: str = "E-Commerce Unified Dashboard"
    debug: bool = True
    cors_origins: list = ["*"]
    use_mock_data: bool = True  # Set to False when API integrations are ready
    
    cafe24: Cafe24Config = Cafe24Config()
    naver: NaverConfig = NaverConfig()
    coupang: CoupangConfig = CoupangConfig()
    
    class Config:
        env_file = ".env"


config = AppConfig()
