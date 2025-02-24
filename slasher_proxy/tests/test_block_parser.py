from typing import Any, Dict

from pony.orm import db_session

from slasher_proxy.avalanche.block_parser import parse_and_save_block
from slasher_proxy.common.model import Block, BlockTransaction, Transaction

sample_block: Dict[str, Any] = {
    "baseFeePerGas": "0x5d21dba00",
    "blockExtraData": "0x",
    "blockGasCost": "0x0",
    "difficulty": "0x1",
    "extDataGasUsed": "0x0",
    "extDataHash": "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421",
    "extraData": "0x000000000000000000000000000a206f0000000000000000000000000009971e000000000009a8fb00000000000e50a50000000000000000000000000000000000000000000000000000000000000000",
    "gasLimit": "0x7a1200",
    "gasUsed": "0x7a1b9",
    "hash": "0xec8148b1712a372e6ab418358ed0cf2051a1f04f80e6a4f77f352d2ab2f9338a",
    "logsBloom": "0x00200400001020040002000080000000400000000000000020400100000000000000000000000000004000000080010000000000200000002000000000200000000080000200000000004008410000220040000000400000000000000000000000000000020004000000000100024800010000000000840000000030800004000000000000010000000002008000000000000080100010080004004000000810020000002000000002000000000000008080000000000000000001000000010040100802010020001008000000000000000000000000001420000002000020000010141000000000000000001008000800002008000000200000000000000000",
    "miner": "0x0100000000000000000000000000000000000000",
    "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "nonce": "0x0000000000000000",
    "number": "0x57e520",
    "parentHash": "0x7dc8ef36dbac74134798b78406ccce73f926b35a7d11ca22029672bd9d84cd3d",
    "receiptsRoot": "0x8b2a08f91826aa3201bbf866a8588080dde8aaeb448caf9c6035b5c0b8f593b1",
    "sha3Uncles": "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347",
    "size": "0x8f2",
    "stateRoot": "0xfb149ac2f5fc1d9159964d9de2e1ae30b3608273fff78fcc8fb15c1b76a47625",
    "timestamp": "0x616c6f77",
    "totalDifficulty": "0x57e520",
    "transactions": [
        {
            "blockHash": "0xec8148b1712a372e6ab418358ed0cf2051a1f04f80e6a4f77f352d2ab2f9338a",
            "blockNumber": "0x57e520",
            "from": "0xeaafb37750164977e8e0269063d88ec521329fc8",
            "gas": "0x1e8480",
            "gasPrice": "0x5d21dba00",
            "hash": "0x1a1b60c7f1f5251d3ced80fe2bae79090824ce2a0f4769b309cb4fdc7c510beb",
            "input": "0x5c11d79500000000000000000000000000000000000000000000002259a2be918f26000000000000000000000000000000000000000000000000000061903b8d49d46a2e00000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000eaafb37750164977e8e0269063d88ec521329fc800000000000000000000000000000000000000000000000000000000616c7d840000000000000000000000000000000000000000000000000000000000000002000000000000000000000000b27c8941a7df8958a1778c0259f76d1f8b711c35000000000000000000000000b31f66aa3c1e785363f0875a1b74e27b85fd66c7",
            "nonce": "0x6d6",
            "to": "0x60ae616a2155ee3d9a68541ba4544862310933d4",
            "transactionIndex": "0x0",
            "value": "0x0",
            "type": "0x0",
            "chainId": "0xa86a",
            "v": "0x150f8",
            "r": "0x7606ef21cd17ea0b744046adcc13478c6530494dfb989bf9cd5e964359f1bbe3",
            "s": "0xd27479d23b42c126d5e16422dd03f3cbc30ae2897eaa6f788a233e4e210d5b5",
        },
        {
            "blockHash": "0xec8148b1712a372e6ab418358ed0cf2051a1f04f80e6a4f77f352d2ab2f9338a",
            "blockNumber": "0x57e520",
            "from": "0x0000000dfda7c426a5273df75536ffc09708c4d8",
            "gas": "0xf4240",
            "gasPrice": "0x5d21dba00",
            "hash": "0xbd57db9633b1afdf0d956b7206fa0e9ee5b1a18f2032ccfb3bc29d7d48baf691",
            "input": "0x4a06c6db00000000000000000000000000000000000000000000000000000000000000800000000000000000000000000000000000000000000000000000000000000120000000000000000000000000000000000000000000000000000000000000018000000000000000000000000000000000000000000000000000000000000000004000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000047fd40c95d362d40000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000047fd40c95d362d400000000000000000000000000000000000000000000000000000000000000002000000000000000000000000c10f947e9ffffac56a8ace7eca988c494f72d9f0000000000000000000000000b2ff0817ad078c92c3afb82326592e06c92581b80000000000000000000000000000000000000000000000000000000000000003000000000000000000000000b31f66aa3c1e785363f0875a1b74e27b85fd66c7000000000000000000000000b27c8941a7df8958a1778c0259f76d1f8b711c35000000000000000000000000b31f66aa3c1e785363f0875a1b74e27b85fd66c7000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000003ec0000000000000000000000000000000000000000000000000000000000000000",
            "nonce": "0x1a79",
            "to": "0x000000004edf117e7d051d0de2712a5c527678b3",
            "transactionIndex": "0x1",
            "value": "0x0",
            "type": "0x0",
            "chainId": "0xa86a",
            "v": "0x150f7",
            "r": "0xad8d11988b7390e0cf1e7634efa2a0ff08c75b9fe94862edf7574c613f75836",
            "s": "0x3612e6250668b9e449b5fdd495406a6dd81e5af085e84ddb93c00498d4ac35f6",
        },
        {
            "blockHash": "0xec8148b1712a372e6ab418358ed0cf2051a1f04f80e6a4f77f352d2ab2f9338a",
            "blockNumber": "0x57e520",
            "from": "0x8a334404308007167eae98919e1dcde4018608fc",
            "gas": "0x2cded",
            "gasPrice": "0x5d21dba00",
            "hash": "0xfd3d7efc8b4b31624e17d378901dd2c9dc27b9a52b6a887f6029f7f654a0db80",
            "input": "0x676528d1000000000000000000000000000000000000000000000038ebad5cdc902800000000000000000000000000000000000000000000000000025cd210ebca86ef8d00000000000000000000000000000000000000000000000000000000000000a00000000000000000000000008a334404308007167eae98919e1dcde4018608fc0000000000000000000000000000000000000000000000000000017c8f94db9a0000000000000000000000000000000000000000000000000000000000000002000000000000000000000000e1c110e1b1b4a1ded0caf3e42bfbdbb7b5d7ce1c000000000000000000000000b31f66aa3c1e785363f0875a1b74e27b85fd66c7",
            "nonce": "0x1f1",
            "to": "0x60ae616a2155ee3d9a68541ba4544862310933d4",
            "transactionIndex": "0x2",
            "value": "0x0",
            "type": "0x0",
            "chainId": "0xa86a",
            "v": "0x150f8",
            "r": "0x2fe07e0519a8481bc33838aa9822df57a3c751dcb1b330aecff9ed5b294dd5a4",
            "s": "0xced426193a6acaaa80cee43294a36562a4d2b91a103a49493552d4cab1e7ecf",
        },
        {
            "blockHash": "0xec8148b1712a372e6ab418358ed0cf2051a1f04f80e6a4f77f352d2ab2f9338a",
            "blockNumber": "0x57e520",
            "from": "0x1c4ebbee1470993473825fd548c48aab22b7c345",
            "gas": "0x39c7b",
            "gasPrice": "0x5d21dba00",
            "maxFeePerGas": "0x5d21dba00",
            "maxPriorityFeePerGas": "0x5d21dba00",
            "hash": "0xf1b45b9dcf5970624a042d2f82124ce2689f90b4dcf990e035e880383a312c51",
            "input": "0x441a3e700000000000000000000000000000000000000000000000000000000000000018000000000000000000000000000000000000000000000009893c2f9e427793ee",
            "nonce": "0x14",
            "to": "0xd6a4f121ca35509af06a0be99093d08462f53052",
            "transactionIndex": "0x3",
            "value": "0x0",
            "type": "0x2",
            "accessList": [],
            "chainId": "0xa86a",
            "v": "0x1",
            "r": "0x3455e41b2d99607f0911b70603487ed223bc38c1324d781df39710f118a0791e",
            "s": "0x77eb7573fe24eaa9548b6e89730da4ba338c319a055b6bbb050e5ecfab771a93",
            "yParity": "0x1",
        },
    ],
    "transactionsRoot": "0x002cb0567dccea3f36059008cbf1dd5d25a52bbf4abde4eb4b58db9a26cd2ca4",
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
