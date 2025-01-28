from typing import Awaitable, Callable

import traceback

from fastapi import Request
from starlette.responses import JSONResponse, Response


async def debug_exception_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    try:
        return await call_next(request)
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "traceback": traceback.format_exc()},
        )
