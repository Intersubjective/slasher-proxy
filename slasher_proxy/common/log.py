import logging
from logging import Logger


def setup_logging() -> Logger:
    logging.basicConfig(
        format="%(levelname)s | %(asctime)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Adjust log levels for specific loggers if needed
    # logging.getLogger("uvicorn").setLevel(logging_level)
    # logging.getLogger("uvicorn.access").setLevel(logging_level)
    logger = logging.getLogger("slasher-proxy")
    return logger


LOGGER: Logger = setup_logging()
