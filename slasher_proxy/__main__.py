from slasher_proxy.asgi import create_slasher_app

# Running as a module in ASGI mode, exposing the app object
# for Uvicorn to find
app = create_slasher_app()
