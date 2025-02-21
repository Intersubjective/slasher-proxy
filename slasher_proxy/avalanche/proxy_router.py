# proxy_router.py
from typing import Annotated

import json

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pony.orm import db_session

from slasher_proxy.common import C_STATUS_PENDING, T_STATUS_SUBMITTED
from slasher_proxy.common.model import Commitment, NodeStats, Transaction
from slasher_proxy.common.settings import SlasherRpcProxySettings, get_settings

router = APIRouter()


@router.post("/eth_sendRawTransaction")
async def handle_send_raw_transaction(
    request: Request,
    settings: Annotated[SlasherRpcProxySettings, Depends(get_settings)],
) -> JSONResponse:
    body = await request.json()
    if body.get("method") != "eth_sendRawTransaction":
        raise HTTPException(status_code=400, detail="Invalid method")
    if (
        "params" not in body
        or not isinstance(body["params"], list)
        or len(body["params"]) != 1
    ):
        raise HTTPException(status_code=400, detail="Invalid params")
    raw_content = json.dumps(body).encode("utf-8")  # Convert JSON to bytes

    # Forward the request to the validator node.
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(settings.rpc_url, json=body) as response:
                response_data = await response.json()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error forwarding to validator: {str(e)}"
        )

    # Check for errors in the response.
    if "error" in response_data:
        error_message = response_data["error"].get("message", "Unknown error")
        raise HTTPException(
            status_code=400, detail=f"Transaction rejected: {error_message}"
        )

    # Validator’s response is expected to include keys "txHash", "commitment", "txIndex"
    result = response_data.get("result")
    if not (isinstance(result, dict) and "txHash" in result and "commitment" in result):
        raise HTTPException(
            status_code=400, detail="Invalid result format from validator"
        )

    tx_hash_hex = result["txHash"]
    commitment_hex = result["commitment"]
    tx_index = result["txIndex"]

    tx_hash = (
        bytes.fromhex(tx_hash_hex[2:])
        if tx_hash_hex.startswith("0x")
        else bytes.fromhex(tx_hash_hex)
    )
    node_commitment = (
        bytes.fromhex(commitment_hex[2:])
        if commitment_hex.startswith("0x")
        else bytes.fromhex(commitment_hex)
    )

    node_id = getattr(settings, "node_id", "avalanche")

    with db_session:
        txn = Transaction.get(hash=tx_hash)
        if not txn:
            txn = Transaction(
                hash=tx_hash,
                raw_content=raw_content,
                status=T_STATUS_SUBMITTED
            )
        Commitment(
            node=node_id,
            tx_hash=tx_hash,
            index=tx_index,
            accumulator=node_commitment,
            status=C_STATUS_PENDING,
        )
        # Update node statistics.
        stats = NodeStats.get(node=node_id)
        if stats:
            stats.total_transactions += 1
        else:
            NodeStats(node=node_id, total_transactions=1)
    return JSONResponse(content=response_data)
