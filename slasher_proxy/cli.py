import click
import uvicorn
from typing import Any

from slasher_proxy.asgi import create_slasher_app
from slasher_proxy.common import db
from slasher_proxy.common.log import LOGGER
from slasher_proxy.common.settings import get_settings


@click.group()
@click.option(
    "--env-file",
    "-e",
    required=False,
    type=click.Path(exists=True),
    help="Path to the .env file",
)
@click.pass_context
def cli(ctx: Any, env_file: str) -> None:
    ctx.ensure_object(dict)
    settings = get_settings(env_file)
    level = settings.log_level or 20
    if isinstance(level, str):
        try:
            level = int(level)
        except ValueError:
            # If conversion fails, leave level as-is
            pass
    LOGGER.setLevel(level)


@cli.command()
@click.pass_context
def avalanche(ctx: Any) -> None:
    settings = get_settings()
    LOGGER.info("Starting Avalanche RPC Proxy...")
    app = create_slasher_app()
    uvicorn.run(app, host=settings.host, port=settings.port)


@cli.command()
@click.pass_context
def upgrade(ctx: Any) -> None:
    db.bind(provider="postgres", **dict(ctx.obj.settings.postgres_connection))
    # upgrade_from_v1(db)
    # upgrade_from_v2(db)
