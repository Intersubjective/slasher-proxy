from typing import Awaitable, Callable

import traceback

from fastapi import Request
from starlette.responses import JSONResponse, Response

from slasher_proxy.common.log import LOGGER


async def debug_exception_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    try:
        return await call_next(request)
    except Exception as exc:
        error_details = {"detail": str(exc), "traceback": traceback.format_exc()}
        LOGGER.error(f"Exception in request: {error_details}")
        return JSONResponse(
            status_code=500,
            content=error_details,
        )
