from typing import AsyncIterator

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .avalanche import proxy_router
from .avalanche.blockchecker import check_block
from .common.database import start_db
from .common.debug_middleware import debug_exception_middleware
from .common.log import LOGGER
from .common.postgres_notify import create_notification_listener
from .common.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    start_db(settings.dsn, network_name=settings.network_name)

    if settings.blocks_channel:
        LOGGER.info("Starting LISTEN to Postgres")
        app.state.block_checker_task = asyncio.create_task(
            create_notification_listener(
                str(settings.dsn), settings.blocks_channel, check_block
            )
        )
    else:
        LOGGER.info(
            "Can't LISTEN to postgres blocks updates: "
            "no NOTIFY channel name provided. "
            "BLOCKS_CHANNEL env var or settings.blocks_channel "
            "field must be set to a valid channel name "
            "for Postgres LISTEN to work correctly!"
        )
        app.state.block_checker_task = None

    yield

    if app.state.block_checker_task:
        LOGGER.info("Stopping LISTEN to Postgres")
        app.state.block_checker_task.cancel()
        await app.state.block_checker_task


def create_slasher_app() -> FastAPI:
    settings = get_settings()
    LOGGER.setLevel(settings.log_level)
    app = FastAPI(title="Slasher RPC Proxy", lifespan=lifespan)

    app.middleware("http")(debug_exception_middleware)
    app.include_router(proxy_router.router)
    LOGGER.info("Returning app instance")

    return app
