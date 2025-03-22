from typing import Any, Dict, cast

import requests
from pony.orm import db_session

from slasher_proxy.common.log import LOGGER
from slasher_proxy.common.model import Block, BlockTransaction, Transaction


def get_cchain_block_by_number(number: int) -> Dict[str, Any]:
    """
    Retrieve a C-Chain block by its number.
    The block number is passed as an integer which we convert to hex.
    """
    url: str = "https://api.avax.network/ext/bc/C/rpc"
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    payload: Dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_getBlockByNumber",
        "params": [hex(number), True],  # 'True' to include full transaction objects
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    response_json = response.json()
    return cast(Dict[str, Any], response_json)


def get_platform_block_by_height(height: int) -> Dict[str, Any]:
    url: str = "https://api.avax.network/ext/bc/P"
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    payload: Dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "platform.getBlockByHeight",
        "params": {"height": height, "encoding": "json"},
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    response_json = response.json()
    return cast(Dict[str, Any], response_json)


def parse_and_save_block(json_data: Dict[str, Any], node_id: str) -> Dict[str, Any]:
    # Extract block data from the top-level "result" key
    result_data = json_data.get("result")
    if not isinstance(result_data, dict):
        raise ValueError("Invalid block JSON. Missing 'result' dict.")

    # Pull hex strings, convert to bytes or int
    block_hash_str = result_data.get("hash")
    height_str = result_data.get("number")
    if not isinstance(block_hash_str, str):
        raise ValueError("Block hash is required.")
    if not isinstance(height_str, str):
        raise ValueError("Block number is required.")

    if block_hash_str.startswith("0x"):
        block_hash = bytes.fromhex(block_hash_str[2:])
    else:
        block_hash = block_hash_str.encode()

    height = int(height_str, 16)
    txs = result_data.get("transactions", [])
    if not isinstance(txs, list):
        raise ValueError("Transactions should be a list.")

    # Save to DB
    with db_session:
        block = Block.get(hash=block_hash)
        if not block:
            block = Block(hash=block_hash, number=height, node_id=node_id)
            LOGGER.info(f"New block created: {height}")

        for i, tx_info in enumerate(txs):
            tx_hash_str = tx_info.get("hash")
            if not isinstance(tx_hash_str, str):
                LOGGER.warning(f"Invalid transaction hash in block {height}, index {i}")
                continue

            if tx_hash_str.startswith("0x"):
                tx_hash = bytes.fromhex(tx_hash_str[2:])
            else:
                tx_hash = tx_hash_str.encode()

            txn = Transaction.get(hash=tx_hash)
            if not txn:
                txn = Transaction(
                    hash=tx_hash,
                    from_address=str(tx_info.get("from") or ""),
                    nonce=int(tx_info.get("nonce") or "0", 16),
                )
                LOGGER.debug(f"New transaction created: {tx_hash_str}")

            BlockTransaction(block=block, transaction=txn, order=i)

    LOGGER.info(f"Block {height} processed with {len(txs)} transactions")
    return {
        "height": height,
        "transaction_count": len(txs),
    }
