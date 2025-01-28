from typing import Annotated

import json

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pony.orm import db_session

from slasher_proxy.common import T_STATUS_ERROR, T_STATUS_SUBMITTED
from slasher_proxy.common.model import Transaction
from slasher_proxy.common.settings import SlasherRpcProxySettings, get_settings

router = APIRouter()


@router.post("/eth_sendRawTransaction")
async def handle_send_raw_transaction(
    request: Request,
    settings: Annotated[SlasherRpcProxySettings, Depends(get_settings)],
) -> JSONResponse:
    body = await request.json()

    # Validate input
    if "method" not in body or body["method"] != "eth_sendRawTransaction":
        raise HTTPException(status_code=400, detail="Invalid method")

    if (
        "params" not in body
        or not isinstance(body["params"], list)
        or len(body["params"]) != 1
    ):
        raise HTTPException(status_code=400, detail="Invalid params")

    try:
        # Forward the request to Avalanche
        async with aiohttp.ClientSession() as session:
            async with session.post(settings.rpc_url, json=body) as response:
                response_data = await response.json()

        # Save the response to the database
        with db_session:
            Transaction(
                hash=bytes.fromhex(
                    response_data.get("result", "")[2:]
                ),  # Convert hex string to bytes
                status=T_STATUS_SUBMITTED if response.status == 200 else T_STATUS_ERROR,
                raw_content=json.dumps(
                    response_data
                ).encode(),  # Convert dict to JSON string, then to bytes
            )

        # Return the response from Avalanche
        return JSONResponse(content=response_data)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error relaying transaction: {str(e)}"
        )
