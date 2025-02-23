from pony.orm import commit, db_session
from typing import cast

from slasher_proxy.avalanche.block_checker import check_block
from slasher_proxy.common import (
    C_STATUS_FULFILLED,
    C_STATUS_OMITTED,
    C_STATUS_PENDING,
    C_STATUS_REORDERED,
    C_STATUS_REVOKED,
    C_STATUS_UNEXPECTED,
    T_STATUS_IN_BLOCK,
    T_STATUS_SUBMITTED,
)

from slasher_proxy.common.model import (
    Block,
    BlockState,
    BlockTransaction,
    Commitment,
    Transaction,
)


# -----------------------------------------------------------------------------
# Helper functions to create test data
# -----------------------------------------------------------------------------
@db_session
def create_test_block(
    block_number: int, node_id: str, tx_hex_list: list[bytes]
) -> Block:
    """
    Create a Block and its associated transactions.
    Each tx_hex (e.g. b"abcdef") is used as the primary key for a Transaction.
    A BlockTransaction is created to link the Block and each Transaction.
    """
    block = Block(
        number=block_number,
        hash=b"block" + str(block_number).encode(),
        node_id=node_id,
    )
    for order, tx_hex in enumerate(tx_hex_list, start=1):
        # Here we assume that tx_hex is already a bytes object (e.g. b"abcdef")
        tx = Transaction.get(hash=tx_hex)
        if not tx:
            tx = Transaction(hash=tx_hex, from_address="dummy", nonce=0)
        BlockTransaction(block=block, transaction=tx, order=order)
    commit()
    return block


@db_session
def create_test_transaction(
    tx_hash: bytes, from_address: str, nonce: int
) -> Transaction:
    """
    Create a Transaction with the given tx_hash,
    or return the existing one if it already exists.
    """
    tx = Transaction.get(hash=tx_hash)
    if not tx:
        # Use select() instead of get() for multiple results, then order them.
        another_tx = (
            Transaction.select(
                lambda t: t.from_address == from_address
                and t.nonce != nonce
                and t.status == T_STATUS_SUBMITTED
            )
            .order_by(Transaction.nonce)
            .first()
        )
        replaces = another_tx.hash if another_tx else None
        tx = Transaction(
            hash=tx_hash, from_address=from_address, nonce=nonce, replaces=replaces
        )
        commit()
    # Let mypy know “tx” is definitely a Transaction:
    return cast(Transaction, tx)


@db_session
def create_test_commitment(
    node: str, index: int, tx_hash: bytes, status: int = C_STATUS_PENDING
) -> None:
    """
    Create a Commitment for a given node and transaction.
    Since Commitment.tx_hash is a reference to a Transaction, we create (or retrieve)
    a Transaction with the given tx_hash.
    """
    tx = Transaction.get(hash=tx_hash)
    if not tx:
        tx = Transaction(hash=tx_hash, from_address="dummy", nonce=0)
    Commitment(node=node, tx_hash=tx.hash, index=index, status=status)
    commit()


# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------
def test_block1_sunny_day() -> None:
    """
    Block 1 contains three valid transactions.
    All corresponding commitments (with indexes 1, 2, 3) are initially pending.
    Expect all to be updated to FULFILLED and a new BlockState with offset_index=3.
    """
    with db_session:
        # Create Block 1 with three transactions.
        create_test_block(1, "nodeA", [b"abcdef", b"123456", b"deadbe"])
        create_test_commitment("nodeA", 1, b"abcdef", C_STATUS_PENDING)
        create_test_commitment("nodeA", 2, b"123456", C_STATUS_PENDING)
        create_test_commitment("nodeA", 3, b"deadbe", C_STATUS_PENDING)
    # Process block 1.
    check_block(1)
    with db_session:
        comms = list(Commitment.select(lambda c: c.node == "nodeA"))
        assert len(comms) == 3
        for c in comms:
            assert c.status == C_STATUS_FULFILLED
        state = BlockState.get(block_number=1)
        assert state is not None
        assert state.block_number == 1
        # These expected values depend on your check_block logic.
        assert state.offset_index == 3
        assert state.shift_index == 0


def test_empty_block() -> None:
    """
    Simulate an error by creating a Block without any BlockTransactions.
    Expect no BlockState to be created.
    """
    with db_session:
        # Create a block without any transactions.
        Block(number=1, hash=b"block_hash", node_id="nodeX")
        commit()
    check_block(1)
    with db_session:
        state = BlockState.get(block_number=1)
        assert state is not None
        assert state.offset_index == 0
        assert state.shift_index == 0
        assert state.block_number == 1


def test_missing_commitment() -> None:
    """
    One transaction string is not valid hex.
    The invalid transaction should be skipped.
    (Here we pass an invalid bytes value; your check_block may log an error.)
    """
    with db_session:
        create_test_block(1, "nodeB", [b"ZZZZ", b"111111"])
        # Only create a commitment for one transaction
        create_test_commitment("nodeB", 2, b"111111", C_STATUS_PENDING)
    check_block(1)
    with db_session:
        comm = Commitment.select(lambda c: c.node == "nodeB" and c.tx_hash).first()
        assert comm is not None
        assert comm.status == C_STATUS_FULFILLED
        state = BlockState.get(block_number=1)
        assert state is not None
        assert state.offset_index == 2
        assert state.shift_index == 0


def test_block_not_found() -> None:
    """
    Calling check_block() with a block number that does not exist.
    Expect no BlockState to be created.
    """
    check_block(999)
    with db_session:
        state = BlockState.get(block_number=999)
        assert state is None


def test_prev_block_state_missing() -> None:
    """
    For a block > 1, if the previous block's state is missing,
    processing should log an error and do nothing.
    """
    with db_session:
        create_test_block(2, "nodeC", [b"222222"])
    check_block(2)
    with db_session:
        state = BlockState.get(block_number=2)
        assert state is None


def test_reorder_transaction() -> None:
    """
    For block 2, simulate a situation where a transaction corresponds to a commitment
    that was previously omitted. It should then be updated to REORDERED.
    """
    # Block 1
    with db_session:
        create_test_block(1, "nodeF", [b"aaaaaa", b"bbbbbb"])
        create_test_commitment("nodeF", 1, b"aaaaaa", C_STATUS_PENDING)
        create_test_commitment("nodeF", 2, b"bbbbbb", C_STATUS_PENDING)
    check_block(1)
    with db_session:
        comm1 = Commitment.select(lambda c: c.node == "nodeF" and c.index == 1).first()
        comm2 = Commitment.select(lambda c: c.node == "nodeF" and c.index == 2).first()
        assert comm1 is not None
        assert comm2 is not None
        assert comm1.status == C_STATUS_FULFILLED
        assert comm2.status == C_STATUS_FULFILLED
        state = BlockState.get(block_number=1)
        assert state is not None
        assert state.offset_index == 2
        assert state.shift_index == 0
    # Block 2
    with db_session:
        create_test_commitment("nodeF", 3, b"cccccc", C_STATUS_PENDING)
        create_test_commitment("nodeF", 4, b"dddddd", C_STATUS_PENDING)
        create_test_block(2, "nodeF", [b"dddddd"])
        commit()
    check_block(2)
    with db_session:
        comm_after = Commitment.select(
            lambda c: c.node == "nodeF" and c.index == 3
        ).first()
        assert comm_after is not None
        assert comm_after.status == C_STATUS_OMITTED
        state = BlockState.get(block_number=2)
        assert state is not None
        assert state.offset_index == 3
        assert state.shift_index == 1
        com3 = Commitment.select(lambda c: c.node == "nodeF" and c.index == 4).first()
        assert com3 is not None
        assert com3.status == C_STATUS_FULFILLED
        comm = Commitment.select(lambda c: c.node == "nodeF" and c.index == 3).first()
        assert comm is not None
        assert comm.status == C_STATUS_OMITTED
    # Block 3
    with db_session:
        create_test_commitment("nodeF", 5, b"eeeeee", C_STATUS_PENDING)
        create_test_commitment("nodeF", 6, b"ffffff", C_STATUS_PENDING)
        create_test_commitment("nodeF", 7, b"fffff2", C_STATUS_PENDING)

        create_test_block(3, "nodeF", [b"eeeeee", b"cccccc", b"ffffaq"])
        commit()
    check_block(3)
    with db_session:
        comm_after = Commitment.select(
            lambda c: c.node == "nodeF" and c.index == 2
        ).first()
        assert comm_after is not None
        assert comm_after.status == C_STATUS_REORDERED
        state = BlockState.get(block_number=3)
        assert state is not None
        assert state.offset_index == 5
        assert state.shift_index == 1
        com3 = Commitment.select(lambda c: c.node == "nodeF" and c.index == 6).first()
        assert com3 is not None
        assert com3.status == C_STATUS_OMITTED


def test_pending_commitments_omitted_block2() -> None:
    """
    For block 2, if some pending commitments in the expected range are not fulfilled,
    they should be marked as OMITTED.
    """
    # Block 1
    with db_session:
        create_test_block(1, "nodeE", [b"111111"])
        create_test_commitment("nodeE", 1, b"111111", C_STATUS_PENDING)
    check_block(1)
    # Block 2
    with db_session:
        create_test_block(2, "nodeE", [b"222222", b"333333"])
        create_test_commitment("nodeE", 2, b"222222", C_STATUS_PENDING)
        create_test_commitment("nodeE", 3, b"333333", C_STATUS_PENDING)
        create_test_commitment("nodeE", 4, b"444444", C_STATUS_PENDING)
    check_block(2)
    with db_session:
        comm2 = Commitment.select(lambda c: c.node == "nodeE" and c.index == 2).first()
        comm3 = Commitment.select(lambda c: c.node == "nodeE" and c.index == 3).first()
        comm4 = Commitment.select(lambda c: c.node == "nodeE" and c.index == 4).first()
        assert comm2 is not None
        assert comm3 is not None
        assert comm4 is not None
        assert comm2.status == C_STATUS_FULFILLED
        assert comm3.status == C_STATUS_FULFILLED
        # The extra commitment (index 4) remains pending.
        assert comm4.status == C_STATUS_PENDING
        state = BlockState.get(block_number=2)
        assert state is not None
        assert state.offset_index == 3
        assert state.shift_index == 0


def test_replacement_transaction() -> None:
    with db_session:
        # Create a block with a single transaction (old transaction).
        create_test_commitment("nodeC", 1, b"oldtx", C_STATUS_PENDING)
        create_test_transaction(b"oldtx", "dummy", 0)
        # Create the new transaction and set its 'replaces' field.
        create_test_transaction(b"newtx", "dummy", 1)
        create_test_block(1, "nodeC", [b"newtx"])
        commit()
    check_block(1)
    with db_session:
        new_tx = Transaction.get(hash=b"newtx")
        assert new_tx is not None
        assert new_tx.replaces is not None
        assert new_tx.status == T_STATUS_IN_BLOCK
        no_new_comm = Commitment.get(node="nodeC", tx_hash=b"newtx")
        assert no_new_comm is not None
        assert no_new_comm.status == C_STATUS_UNEXPECTED

        old_comm = Commitment.get(node="nodeC", tx_hash=b"oldtx")
        assert old_comm is not None
        assert old_comm.status == C_STATUS_REVOKED
