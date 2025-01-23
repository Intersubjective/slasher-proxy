import click
import uvicorn

from slasher_proxy.asgi import create_slasher_app
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
def cli(ctx, env_file):
    ctx.ensure_object(dict)
    settings = get_settings(env_file)
    LOGGER.setLevel(settings.log_level)


@cli.command()
@click.pass_context
def avalanche(ctx):
    settings = get_settings()
    LOGGER.info("Starting Avalanche RPC Proxy...")
    app = create_slasher_app()
    uvicorn.run(app, host=settings.host, port=settings.port)


@cli.command()
@click.pass_context
def upgrade(ctx):
    db.bind(provider="postgres", **dict(ctx.obj.settings.postgres_connection))
    # upgrade_from_v1(db)
    # upgrade_from_v2(db)
