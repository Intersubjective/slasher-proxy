# accumulator.py
from typing import List

import hashlib


def int_to_bytes(x: int, length: int = 4) -> bytes:
    """Convert an integer to a fixed-length big-endian byte string."""
    return x.to_bytes(length, byteorder="big")


class RollingHashAccumulator:
    """
    A simple rolling-hash accumulator using linear chaining.
    Every appended transaction updates the state with:
         H_new = SHA256( H_prev || (global_index) || tx_hash )
    The global index is defined as:
         global_index = initial_count + number_of_appended_transactions + 1
    This supports deletion by recomputing the state from the initial state.
    """

    def __init__(
        self, initial_state: bytes = b"\x00" * 32, initial_count: int = 0
    ) -> None:
        self.initial_state: bytes = initial_state  # original state
        self.state: bytes = initial_state
        self.initial_count: int = initial_count  # shift for global indices
        self.tx_hashes: List[bytes] = []  # stored appended transaction hashes

    def add_transaction(self, tx_hash: bytes) -> int:
        """
        Append a transaction hash and update accumulator state.
        Returns the new global index (1-indexed with a shift).
        """
        new_index: int = self.initial_count + len(self.tx_hashes) + 1
        self.tx_hashes.append(tx_hash)
        self.state = hashlib.sha256(
            self.state + int_to_bytes(new_index) + tx_hash
        ).digest()
        return new_index

    def delete_transaction(self, global_index: int) -> None:
        """
        Delete the transaction at the given global index.
        The global index must be at least initial_count+1.
        After deletion, the state is recomputed by processing remaining transactions.
        Raises IndexError if the provided index does not correspond to an appended tx.
        """
        # Compute local index (0-based) for the appended list.
        local_index: int = global_index - self.initial_count - 1
        if local_index < 0 or local_index >= len(self.tx_hashes):
            raise IndexError("Transaction global index out of range")
        del self.tx_hashes[local_index]
        # Recompute state from the initial state using shifted indices.
        self.state = self.initial_state
        for i, tx in enumerate(self.tx_hashes, start=1):
            idx: int = self.initial_count + i
            self.state = hashlib.sha256(self.state + int_to_bytes(idx) + tx).digest()

    def to_bytes(self) -> bytes:
        """Return the current accumulator state."""
        return self.state

    @property
    def total_count(self) -> int:
        return self.initial_count + len(self.tx_hashes)
