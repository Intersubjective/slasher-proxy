# block_checker.py

from pony.orm import db_session

from slasher_proxy.common import (
    C_STATUS_FULFILLED,
    C_STATUS_OMITTED,
    C_STATUS_PENDING,
    C_STATUS_REORDERED,
    C_STATUS_REVOKED,
    C_STATUS_UNEXPECTED,
    T_STATUS_IN_BLOCK,
)
from slasher_proxy.common.log import LOGGER
from slasher_proxy.common.model import Block, BlockState, Commitment, Transaction


@db_session
def check_block(block_number: int) -> None:
    """
    Check the block and update the commitment status.
    """
    LOGGER.info(f"Processing block {block_number} for verification.")
    block = Block.get(number=block_number)
    if not block:
        LOGGER.error(f"Block {block_number} not found in database.")
        return

    node_id = block.node_id
    tx_list = block.block_transactions

    LOGGER.info(f"Block {block_number} contains {len(tx_list)} transactions.")

    prev_block_state = BlockState.get(block_number=block_number - 1)
    if not prev_block_state:
        LOGGER.warning(
            f"State for block {block_number - 1} not found. Initializing new state."
        )
        offset_index = 0
        shift_index = 0
    else:
        offset_index = prev_block_state.offset_index
        shift_index = prev_block_state.shift_index

    reordered_txs = 0
    start_range = offset_index + 1
    processed_indexes = set()
    current_order = 0
    for tx in tx_list:
        current_order = tx.order
        tx_hash = tx.transaction.hash
        comm = Commitment.get(node=node_id, tx_hash=tx_hash)
        tx_obj = Transaction.get(hash=tx_hash)
        if tx_obj:
            tx_obj.status = T_STATUS_IN_BLOCK
            # Check if this transaction is a replacement
            if tx_obj.replaces:
                replaced_tx_hash = tx_obj.replaces
                replaced_comm = Commitment.get(node=node_id, tx_hash=replaced_tx_hash)
                if replaced_comm and replaced_comm.status in [
                    C_STATUS_PENDING,
                    C_STATUS_OMITTED,
                ]:
                    replaced_comm.status = C_STATUS_REVOKED
        if comm:
            if comm.status == C_STATUS_OMITTED:
                reordered_txs += 1
                comm.status = C_STATUS_REORDERED
                LOGGER.info(f"Commitment {comm.index} reordered.")
            elif comm.status == C_STATUS_PENDING:
                processed_indexes.add(comm.index)
                comm.status = C_STATUS_FULFILLED
            elif comm.status in [C_STATUS_REORDERED, C_STATUS_FULFILLED]:
                LOGGER.warning(f"Commitment {comm.index} already processed.")
        else:
            LOGGER.info(f"New commitment for tx {tx_hash} found.")
            # Save new commitment
            Commitment(
                node=node_id,
                tx_hash=tx_hash,
                index=current_order + 1,
                status=C_STATUS_UNEXPECTED,
            )
            current_order += 1

    total_new_txs = len(tx_list) - reordered_txs
    end_range = start_range + total_new_txs + shift_index
    processing_range = set(range(start_range, end_range))
    out_of_range_txs = len(processed_indexes - processing_range)

    commitments = Commitment.select(
        lambda c: c.status == C_STATUS_PENDING
        and c.node == node_id
        and c.index >= start_range
        and c.index < end_range
    ).order_by(Commitment.index)[:total_new_txs]
    for c in commitments:
        c.status = C_STATUS_OMITTED
    shift_index += out_of_range_txs
    offset_index += total_new_txs
    BlockState(
        block_number=block_number,
        offset_index=offset_index,
        shift_index=shift_index,
    )
    LOGGER.info(f"Block {block_number} processed.")
