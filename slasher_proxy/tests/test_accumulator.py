import hashlib

from slasher_proxy.common.accumulator import RollingHashAccumulator


def int_to_bytes(x: int, length: int = 4) -> bytes:
    return x.to_bytes(length, byteorder="big")


def compute_expected_state(
    initial_state: bytes, txs: list[bytes], shift: int = 0
) -> bytes:
    state = initial_state
    # Global index starts at shift+1.
    for i, tx in enumerate(txs, start=1):
        idx = shift + i
        state = hashlib.sha256(state + int_to_bytes(idx) + tx).digest()
    return state


def test_initial_state() -> None:
    """Accumulator should return the initial state with no transactions."""
    init_state = b"\xAA" * 32
    acc = RollingHashAccumulator(initial_state=init_state, initial_count=10)
    # No appended transactions, so global total equals initial_count.
    assert acc.total_count == 10
    assert acc.to_bytes() == init_state


def test_add_single_transaction() -> None:
    """Adding one transaction updates the state and returns shifted index."""
    init_state = b"\x00" * 32
    tx = b"tx1"
    acc = RollingHashAccumulator(initial_state=init_state)
    idx = acc.add_transaction(tx)
    # With default shift 0, first transaction obtains index 1.
    expected_state = hashlib.sha256(init_state + int_to_bytes(1) + tx).digest()
    assert idx == 1
    assert acc.total_count == 1
    assert acc.to_bytes() == expected_state


def test_sequential_transactions() -> None:
    """Adding multiple transactions sequentially should yield
    expected state using shift."""
    init_state = b"\x00" * 32
    transactions = [b"tx1", b"tx2", b"tx3"]
    shift = 5
    acc = RollingHashAccumulator(initial_state=init_state, initial_count=shift)
    for tx in transactions:
        acc.add_transaction(tx)
    expected = compute_expected_state(init_state, transactions, shift)
    assert acc.total_count == shift + len(transactions)
    assert acc.to_bytes() == expected


def test_repeated_transactions() -> None:
    """Repeated (even identical) transactions yield unique state because of shifted indices."""
    init_state = b"\x00" * 32
    tx = b"duplicate_tx"
    tx2 = b"duplicate2_tx"
    acc1 = RollingHashAccumulator(initial_state=init_state)
    acc1.add_transaction(tx)

    acc2 = RollingHashAccumulator(initial_state=init_state)
    acc2.add_transaction(tx2)

    # States must not be equal.
    assert acc1.to_bytes() != acc2.to_bytes()
    assert acc1.total_count == 1
    assert acc2.total_count == 1
