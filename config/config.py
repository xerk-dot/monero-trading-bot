from enum import Enum
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


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

    # News monitoring configuration
    twitter_bearer_token: Optional[str] = Field(default=None)
    news_llm_provider: str = Field(default="openai")  # 'openai' or 'anthropic'
    openai_api_key: Optional[str] = Field(default=None)
    anthropic_api_key: Optional[str] = Field(default=None)
    news_llm_model: Optional[str] = Field(default=None)  # Auto-selects if None
    news_monitoring_enabled: bool = Field(default=True)
    news_check_interval_minutes: int = Field(default=30)
    news_aggregation_window_hours: int = Field(default=2)
    news_strategy_weight: float = Field(default=0.10, ge=0.0, le=1.0)

    # Darknet monitoring configuration (optional)
    darknet_monitoring_enabled: bool = Field(default=False)
    darknet_tor_proxy_host: str = Field(default="127.0.0.1")
    darknet_tor_proxy_port: int = Field(default=9050)  # 9050 for system tor, 9150 for Tor Browser
    darknet_update_interval_hours: int = Field(default=24)
    darknet_strategy_weight: float = Field(default=0.05, ge=0.0, le=1.0)
    darknet_bullish_threshold: float = Field(default=60.0, ge=0.0, le=100.0)
    darknet_bearish_threshold: float = Field(default=35.0, ge=0.0, le=100.0)
    darknet_min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # GitHub monitoring configuration
    github_token: Optional[str] = Field(default=None)
    github_monitoring_enabled: bool = Field(default=True)
    github_scrape_interval_hours: int = Field(default=6)
    github_strategy_weight: float = Field(default=0.15, ge=0.0, le=1.0)

    # GCP/BigQuery configuration
    gcp_project_id: Optional[str] = Field(default=None)
    gcp_credentials_path: Optional[str] = Field(default=None)
    bigquery_dataset: str = Field(default="monero_github")

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
    def exchange_credentials(self) -> dict[str, dict[str, str]]:
        creds = {}
        if self.binance_api_key and self.binance_secret:
            creds["binance"] = {"apiKey": self.binance_api_key, "secret": self.binance_secret}
        if self.kraken_api_key and self.kraken_secret:
            creds["kraken"] = {"apiKey": self.kraken_api_key, "secret": self.kraken_secret}
        return creds

    @property
    def llm_api_key(self) -> Optional[str]:
        """Get the appropriate LLM API key based on provider."""
        if self.news_llm_provider == "openai":
            return self.openai_api_key
        elif self.news_llm_provider == "anthropic":
            return self.anthropic_api_key
        return None

    @property
    def news_monitoring_available(self) -> bool:
        """Check if news monitoring can be enabled."""
        has_twitter = bool(self.twitter_bearer_token)
        has_llm = bool(self.llm_api_key)
        return has_twitter and has_llm and self.news_monitoring_enabled

    @property
    def darknet_monitoring_available(self) -> bool:
        """Check if darknet monitoring can be enabled."""
        # Darknet only requires Tor to be running (no API keys needed)
        # We assume if enabled=True, user has Tor configured
        return self.darknet_monitoring_enabled


config = TradingConfig()
