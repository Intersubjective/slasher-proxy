import hashlib

import pytest

from slasher_proxy.common.sketch import CountingBloomFilterAccumulator


def tx_hash(tx_data: bytes) -> bytes:
    """Helper function to hash transaction data."""
    return hashlib.sha256(tx_data).digest()


def test_accumulator_initialization() -> None:
    """Test that the accumulator is initialized correctly."""
    acc = CountingBloomFilterAccumulator()
    assert len(acc.counters) == 64
    assert acc.num_hashes == 1
    assert acc.counter_size == 2
    assert acc.salt is not None


def test_add_transaction() -> None:
    """Test that adding a transaction increments the correct counters."""
    acc = CountingBloomFilterAccumulator(num_counters=16, num_hashes=2)
    tx1 = tx_hash(b"tx1")
    acc.add_transaction(tx1)
    # Check that at least one counter was incremented.
    assert sum(acc.counters) > 0


def test_delete_transaction() -> None:
    """Test that deleting a transaction decrements the correct counters."""
    acc = CountingBloomFilterAccumulator(num_counters=16, num_hashes=2)
    tx1 = tx_hash(b"tx1")
    acc.add_transaction(tx1)
    acc.delete_transaction(tx1)
    # Check that at least one counter was decremented.
    assert sum(acc.counters) == 0


def test_to_bytes_and_from_bytes() -> None:
    """Test that the accumulator can be serialized and deserialized correctly."""
    acc1 = CountingBloomFilterAccumulator(num_counters=32, num_hashes=3, counter_size=2)
    tx1 = tx_hash(b"tx1")
    tx2 = tx_hash(b"tx2")
    acc1.add_transaction(tx1)
    acc1.add_transaction(tx2)
    acc1.delete_transaction(tx1)

    state_bytes = acc1.to_bytes()
    acc2 = CountingBloomFilterAccumulator.from_bytes(
        state_bytes, num_counters=32, num_hashes=3, counter_size=2
    )

    # Check that the counters are the same.
    assert acc1.counters == acc2.counters
    # Check that the parameters are the same.
    assert acc1.num_counters == acc2.num_counters
    assert acc1.num_hashes == acc2.num_hashes
    assert acc1.counter_size == acc2.counter_size
    assert acc1.salt == acc2.salt


def test_large_number_of_transactions() -> None:
    """Test that the accumulator can handle a large number of transactions without overflowing."""
    acc = CountingBloomFilterAccumulator(num_counters=64, num_hashes=1, counter_size=2)
    num_transactions = 100
    for i in range(num_transactions):
        tx = tx_hash(f"tx{i}".encode())
        acc.add_transaction(tx)
    # Check that no counters overflowed (assuming counter_size=2 means max
    # value is 65535).
    assert all(c < 65535 for c in acc.counters)


def test_negative_counter_values() -> None:
    """Test that the accumulator handles negative counter values correctly."""
    acc = CountingBloomFilterAccumulator(num_counters=16, num_hashes=1, counter_size=2)
    tx1 = tx_hash(b"tx1")
    acc.delete_transaction(tx1)
    # Check that at least one counter is negative.
    assert any(c < 0 for c in acc.counters)


def test_different_salt_values() -> None:
    """Test that different salt values result in different accumulator states."""
    acc1 = CountingBloomFilterAccumulator(num_counters=16, num_hashes=1, salt=b"salt1")
    acc2 = CountingBloomFilterAccumulator(num_counters=16, num_hashes=1, salt=b"salt2")
    tx1 = tx_hash(b"tx1")
    acc1.add_transaction(tx1)
    acc2.add_transaction(tx1)
    # Check that the counters are different.
    assert acc1.counters != acc2.counters


def test_collision_resistance() -> None:
    """Test that the accumulator exhibits some collision resistance."""
    acc = CountingBloomFilterAccumulator(num_counters=16, num_hashes=1)
    tx1 = tx_hash(b"tx1")
    tx2 = tx_hash(b"tx2")  # Assuming tx1 and tx2 don't collide perfectly
    acc.add_transaction(tx1)
    acc.add_transaction(tx2)
    # Check that the counters are not all the same.
    assert len(set(acc.counters)) > 1


def test_from_bytes_with_different_parameters() -> None:
    """Test that from_bytes raises an exception if parameters don't match."""
    acc1 = CountingBloomFilterAccumulator(num_counters=32, num_hashes=1, counter_size=2)
    state_bytes = acc1.to_bytes()
    with pytest.raises(ValueError):
        CountingBloomFilterAccumulator.from_bytes(
            state_bytes, num_counters=16, num_hashes=1, counter_size=2
        )
