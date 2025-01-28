from typing import Optional

import logging
from functools import lru_cache

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings

VALID_LOG_LEVELS = {
    logging.getLevelName(level)
    for level in (
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    )
}


# Pydantic will try to load .env file if it exists. Alternatively, you can manually
# load environment variables from the filename of your choice (if you use cli mode of
# the app). Note that the variables loaded from the .env file will not pass on to the
# whole app, they will be used only to init Pydantic settings. You can altogether use
# just the real environment variables, completely ignoring the .env file.


class SlasherRpcProxySettings(BaseSettings):
    port: int = 5500
    host: str = "0.0.0.0"
    log_level: Optional[str] = Field(default="INFO")
    dsn: PostgresDsn
    blocks_channel: Optional[str] = Field(None)
    rpc_url: str = Field()
    network_name: Optional[str] = Field("avalanche")

    def validate_log_level(cls, v: Optional[str]) -> str:
        if v is None:
            return "INFO"
        v = v.upper()
        if v not in VALID_LOG_LEVELS:
            raise ValueError(f"Invalid log level: {v}")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings_instance: Optional[SlasherRpcProxySettings] = None


@lru_cache()
def get_settings(env_file: Optional[str] = None) -> SlasherRpcProxySettings:
    global settings_instance
    if settings_instance is None or env_file:
        # load_dotenv(env_file) - this one is redundant but maybe useful in future
        settings_instance = (
            # If env_file is not provided, load the settings from the environment
            SlasherRpcProxySettings()  # type: ignore[call-arg]
            if env_file is None
            else SlasherRpcProxySettings(_env_file=env_file)  # type: ignore[call-arg]
        )
    return settings_instance


def set_settings(new_settings: SlasherRpcProxySettings) -> None:
    global settings_instance
    settings_instance = new_settings
    get_settings.cache_clear()
