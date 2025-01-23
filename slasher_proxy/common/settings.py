from typing import Optional

import logging
from functools import lru_cache

from pydantic import Field, PostgresDsn, field_validator
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


# Pydantic will try to load .env file if it exists. Alternatively, you can manually load
# environment variables from the filename of your choice (if you use cli mode of the app).
# Notea that the variables loaded from the .env file will not pass on to the whole app,
# they will be used only to init Pydantic settings.
# You can altogether use just the real environment variables, completely ignoring the .env file.


class SlasherRpcProxySettings(BaseSettings):
    port: int = 5500
    host: str = "0.0.0.0"
    log_level: Optional[str] = Field(default="INFO")
    dsn: PostgresDsn
    blocks_channel: Optional[str] = Field(None)
    rpc_url: str = Field()
    network_name: Optional[str] = Field("avalanche")

    @classmethod
    @field_validator("log_level")
    def validate_log_level(cls, v: Optional[str]) -> str:
        if v is None:
            return logging.INFO

        v_upper = v.upper()
        if v_upper not in VALID_LOG_LEVELS:
            raise ValueError(
                f"Invalid log level. Allowed values are {VALID_LOG_LEVELS}"
            )

        return v_upper

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def create_get_settings():
    settings_instance = None

    @lru_cache()
    def _get_settings(env_file: str = None) -> SlasherRpcProxySettings:
        nonlocal settings_instance
        if settings_instance is None or env_file:
            # load_dotenv(env_file) - this one is redundant but maybe useful in future
            settings_instance = (
                SlasherRpcProxySettings()
                if env_file is None
                else SlasherRpcProxySettings(_env_file=env_file)
            )
        return settings_instance

    def _set_settings(new_settings: SlasherRpcProxySettings):
        nonlocal settings_instance
        settings_instance = new_settings
        get_settings.cache_clear()

    return _get_settings, _set_settings


get_settings, set_settings = create_get_settings()
