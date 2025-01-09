from slasher_proxy.asgi import create_slasher_app
from slasher_proxy.cli import cli

if __name__ == "__main__":
    cli(obj=None)
else:
    # Running as a module in ASGI mode, exposing the app object
    # for Uvicorn to find
    app = create_slasher_app()
