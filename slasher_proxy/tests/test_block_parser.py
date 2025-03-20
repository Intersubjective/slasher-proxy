from typing import Any, Dict

from pony.orm import db_session

from slasher_proxy.avalanche.block_parser import parse_and_save_block
from slasher_proxy.common.model import Block, BlockTransaction, Transaction

sample_block: Dict[str, Any] = {
    "baseFeePerGas": "0x5d21dba00",
    "blobGasUsed": "0x0",
    "blockGasCost": "0x0",
    "difficulty": "0x1",
    "excessBlobGas": "0x0",
    "extraData": "0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "gasLimit": "0xe4e1c0",
    "gasUsed": "0x5208",
    "hash": "0xc589a5072a8db21c940fa4a4a5bb006ed1f50faf596d9ab75d1b09946680c411",
    "logsBloom": "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "miner": "0x0100000000000000000000000000000000000000",
    "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "nonce": "0x0000000000000000",
    "number": "0xf",
    "parentBeaconBlockRoot": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "parentHash": "0x896a93e6bfd427a712eb4e59f40ab2afd77a8b2522b2707e89941b127d80d754",
    "receiptsRoot": "0xf78dfb743fbd92ade140711c8bbc542b5e307f0ab7984eff35d751969fe57efa",
    "sha3Uncles": "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
    "size": "0x2fa",
    "stateRoot": "0xce776bf84c5d73ef299d7d3e204fadccb4a31b266f3ff551a08d876fa909c179",
    "timestamp": "0x67dc5224",
    "totalDifficulty": "0xf",
    "transactions": [
        {
            "blockHash": "0xc589a5072a8db21c940fa4a4a5bb006ed1f50faf596d9ab75d1b09946680c411",
            "blockNumber": "0xf",
            "from": "0xa28fcb2ec5e2112c57ef63292cf85ab61a95ba72",
            "gas": "0x5208",
            "gasPrice": "0x6fc23ac00",
            "maxFeePerGas": "0x6fc23ac00",
            "maxPriorityFeePerGas": "0x12a05f200",
            "hash": "0x522a7d836cf8a0a534deb6cd1f79242444d846089ad995ba56a0ec6a3b6cb075",
            "input": "0x",
            "nonce": "0xe",
            "to": "0xa28fcb2ec5e2112c57ef63292cf85ab61a95ba72",
            "transactionIndex": "0x0",
            "value": "0x38d7ea4c68000",
            "type": "0x2",
            "accessList": [],
            "chainId": "0x192b",
            "v": "0x1",
            "r": "0x866cb73ee7fa7a923a042afd5dfb4675befa4ae0b04458913fd5bfc9ede46fa6",
            "s": "0x14b2c24368689869d9ddce37368cfead6d771b8a9bf05a4f1eaed360a24448bf",
            "yParity": "0x1",
        }
    ],
    "transactionsRoot": "0xc11b9f07c66312e09f0ec669cc1679aa7d3235ab06511e86a760e159789e849f",
    "uncles": [],
}


def test_parse_and_save_block() -> None:
    # Wrap the sample block in a JSON result dict.
    json_result = {"result": sample_block}

    # Provide a node_id here.
    saved = parse_and_save_block(json_result, node_id="test-node")

    # Assert the returned dictionary contains the correct information.
    block_number_str = sample_block["number"]
    assert isinstance(block_number_str, str)
    expected_height = int(block_number_str, 16)

    tx_list = sample_block["transactions"]
    assert isinstance(tx_list, list)
    expected_tx_count = len(tx_list)

    assert saved is not None
    assert saved["height"] == expected_height
    assert saved["transaction_count"] == expected_tx_count

    # Now check that the records were indeed saved in the DB.
    with db_session:
        block = Block.get(number=expected_height)
        assert block is not None

        assert block.block_transactions is not None
        assert len(block.block_transactions) == expected_tx_count

        # Count the blocktransactions for this block.
        block_tx_count = len(BlockTransaction.select(lambda bt: bt.block == block))
        assert block_tx_count == expected_tx_count

        # Additionally, check that each transaction exists.
        for tx in tx_list:
            assert isinstance(tx, dict)
            tx_hash_str = tx.get("hash", "")
            tx_hash = (
                bytes.fromhex(tx_hash_str[2:])
                if tx_hash_str.startswith("0x")
                else tx_hash_str.encode()
            )
            tx_obj = Transaction.get(hash=tx_hash)
            assert tx_obj is not None
