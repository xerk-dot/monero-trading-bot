from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, Dict, Any
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class TradingConfig(BaseSettings):
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    log_level: str = Field(default="INFO")

    binance_api_key: Optional[str] = Field(default=None)
    binance_secret: Optional[str] = Field(default=None)
    kraken_api_key: Optional[str] = Field(default=None)
    kraken_secret: Optional[str] = Field(default=None)

    db_host: str = Field(default="localhost")
    db_port: int = Field(default=5432)
    db_name: str = Field(default="monero_trading")
    db_user: str = Field(default="trading_bot")
    db_password: str = Field(default="")

    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_password: Optional[str] = Field(default=None)

    influxdb_url: str = Field(default="http://localhost:8086")
    influxdb_token: Optional[str] = Field(default=None)
    influxdb_org: str = Field(default="trading_bot")
    influxdb_bucket: str = Field(default="market_data")

    telegram_bot_token: Optional[str] = Field(default=None)
    telegram_chat_id: Optional[str] = Field(default=None)

    max_position_size: float = Field(default=0.02, ge=0.001, le=0.1)
    max_portfolio_exposure: float = Field(default=0.3, ge=0.1, le=1.0)
    min_risk_reward_ratio: float = Field(default=1.5, ge=1.0)
    default_stop_loss_atr_multiplier: float = Field(default=2.5, ge=1.0, le=5.0)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}"
        return f"redis://{self.redis_host}:{self.redis_port}"

    @property
    def exchange_credentials(self) -> Dict[str, Dict[str, str]]:
        creds = {}
        if self.binance_api_key and self.binance_secret:
            creds["binance"] = {
                "apiKey": self.binance_api_key,
                "secret": self.binance_secret
            }
        if self.kraken_api_key and self.kraken_secret:
            creds["kraken"] = {
                "apiKey": self.kraken_api_key,
                "secret": self.kraken_secret
            }
        return creds


config = TradingConfig()