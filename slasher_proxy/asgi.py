from typing import AsyncIterator

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .avalanche import proxy_router
from .avalanche.block_checker import check_block
from .avalanche.block_parser import parse_and_save_block
from .avalanche.ws_blocks import WebSocketListener
from .common.database import start_db
from .common.debug_middleware import debug_exception_middleware
from .common.log import LOGGER
from .common.postgres_notify import create_notification_listener
from .common.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    start_db(settings.dsn, network_name=settings.network_name)

    app.state.block_checker_task = None
    app.state.websocket_listener = None

    if settings.blocks_channel:
        LOGGER.info("Starting LISTEN to Postgres")
        app.state.block_checker_task = asyncio.create_task(
            create_notification_listener(
                str(settings.dsn), settings.blocks_channel, check_block
            )
        )
    elif settings.blocks_websocket_url:
        LOGGER.info("Starting listening to websocket for new blocks")
        app.state.websocket_listener = WebSocketListener(
            settings.blocks_websocket_url, parse_and_save_block, check_block
        )
        app.state.block_checker_task = asyncio.create_task(
            app.state.websocket_listener.listen()
        )
    else:
        LOGGER.info(
            "Can't LISTEN to postgres blocks updates: "
            "no NOTIFY channel name or websocket URL is provided."
            "BLOCKS_CHANNEL env var or settings.blocks_channel "
            "field must be set to a valid channel name "
            "for Postgres LISTEN to work correctly!"
        )

    try:
        yield
    finally:
        if app.state.block_checker_task:
            LOGGER.info("Stopping LISTEN to Postgres")
            app.state.block_checker_task.cancel()


def create_slasher_app() -> FastAPI:
    settings = get_settings()
    level = settings.log_level  # str | None
    if level is None:
        level_num = 20
    elif level.isdigit():
        level_num = int(level)
    else:
        level_num = 20
    LOGGER.setLevel(level_num)
    app = FastAPI(title="Slasher RPC Proxy", lifespan=lifespan)

    app.middleware("http")(debug_exception_middleware)
    app.include_router(proxy_router.router)
    LOGGER.info("Returning app instance")

    return app
