from setuptools import setup, find_packages

setup(
    name="monero-trading-bot",
    version="1.0.0",
    description="Monero Privacy Coin Swing Trading Bot",
    author="Trading Bot System",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.1.4",
        "numpy>=1.26.2",
        "ccxt>=4.2.25",
        "ta-lib>=0.4.28",
        "pandas-ta>=0.3.14b",
        "psycopg2-binary>=2.9.9",
        "sqlalchemy>=2.0.25",
        "redis>=5.0.1",
        "influxdb-client>=1.40.0",
        "scikit-learn>=1.4.0",
        "xgboost>=2.0.3",
        "lightgbm>=4.3.0",
        "aiohttp>=3.9.1",
        "websockets>=12.0",
        "prometheus-client>=0.19.0",
        "python-telegram-bot>=21.0.1",
        "pydantic>=2.5.3",
        "pydantic-settings>=2.1.0",
        "python-dotenv>=1.0.0"
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "monero-bot=main:main",
        ],
    },
)