import json
from pony.orm import db_session
from slasher_proxy.common.log import LOGGER
from slasher_proxy.common.model import Block, Commitment, AuxiliaryData
from slasher_proxy.common.sketch import ClockSketch, clocks_inconsistent


def check_block(notification_from_postgres):
    num_block = int(notification_from_postgres)
    LOGGER.info(f"Block {num_block} notification received")
    with db_session:
        block = Block.get(number=num_block)
    if block is None:
        LOGGER.warning(f"Block {num_block} not found in the database")
        return
    LOGGER.info(f"Block {num_block} hash {block.hash.hex()}")

    try:
        block_data = json.loads(block.raw_content.decode())
    except Exception as e:
        LOGGER.error(f"Error decoding block content: {e}")
        return

    tx_list = block_data.get("transactions", [])
    if not tx_list:
        LOGGER.info("No transactions in block")
        return

    # Process the block for each node. In this example we assume a single node "avalanche".
    # Extend this list if you expect transactions from multiple nodes.
    node_ids = ["avalanche"]

    for node_id in node_ids:
        # Retrieve the stored sketch state (and last processed index) for this node.
        with db_session:
            aux_sketch = AuxiliaryData.get(key=f"last_block_sketch_{node_id}")
            aux_index = AuxiliaryData.get(key=f"last_block_index_{node_id}")
            if aux_sketch and aux_sketch.value:
                try:
                    block_sketch = ClockSketch.from_bytes(bytes.fromhex(aux_sketch.value))
                    last_index = int(aux_index.value) if aux_index and aux_index.value.isdigit() else 0
                except Exception as e:
                    LOGGER.error(f"Error reconstructing sketch for node {node_id}: {e}")
                    block_sketch = ClockSketch(n_cells=32)
                    last_index = 0
            else:
                block_sketch = ClockSketch(n_cells=32)
                last_index = 0

        # Process each transaction from the block for this node.
        for i, tx_hex in enumerate(tx_list):
            try:
                tx_bytes = (
                    bytes.fromhex(tx_hex[2:])
                    if tx_hex.startswith("0x")
                    else bytes.fromhex(tx_hex)
                )
                item_val = int.from_bytes(tx_bytes, byteorder="big")
                block_sketch.increment(item_val)
                current_index = last_index + i

                with db_session:
                    commitment = Commitment.get(node=node_id, index=current_index)
                if commitment:
                    clocks_inconsistent(block_sketch.to_bytes(), commitment.sketch)
                    


                    if block_sketch.to_bytes() != commitment.sketch:
                        LOGGER.error(f"Inconsistency detected at tx index {current_index} for node {node_id}")
                    else:
                        LOGGER.info(f"Commitment at index {current_index} for node {node_id} is consistent")
                else:
                    LOGGER.warning(f"No commitment record found for tx index {current_index} for node {node_id}")
            except Exception as e:
                LOGGER.error(f"Error processing transaction {tx_hex} for node {node_id}: {e}")

        # After processing, update AuxiliaryData so that the next block check starts from the new state.
        new_index = last_index + len(tx_list)
        with db_session:
            if aux_sketch:
                aux_sketch.value = block_sketch.to_bytes().hex()
            else:
                AuxiliaryData(key=f"last_block_sketch_{node_id}", value=block_sketch.to_bytes().hex())
            if aux_index:
                aux_index.value = str(new_index)
            else:
                AuxiliaryData(key=f"last_block_index_{node_id}", value=str(new_index))
