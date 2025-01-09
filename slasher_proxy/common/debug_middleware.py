from fastapi import Request
from fastapi.responses import JSONResponse
import traceback

async def debug_exception_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "traceback": traceback.format_exc()
            }
        )
