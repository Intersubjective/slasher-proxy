import logging


def setup_logging():
    logging.basicConfig(
        format="%(levelname)s | %(asctime)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Adjust log levels for specific loggers if needed
    # logging.getLogger("uvicorn").setLevel(logging_level)
    # logging.getLogger("uvicorn.access").setLevel(logging_level)
    return logging.getLogger("slasherproxy")


LOGGER = setup_logging()
