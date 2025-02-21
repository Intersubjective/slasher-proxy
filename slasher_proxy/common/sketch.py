import hashlib
import random

DEFAULT_NUM_COUNTERS = 64
DEFAULT_NUM_HASHES = 1
DEFAULT_COUNTER_SIZE = 2


class CountingBloomFilterAccumulator:
    def __init__(self, num_counters=DEFAULT_NUM_COUNTERS, num_hashes=DEFAULT_NUM_HASHES,
                 counter_size=DEFAULT_COUNTER_SIZE, salt=None):
        self.num_counters = num_counters
        self.num_hashes = num_hashes
        self.counter_size = counter_size  # in bytes
        self.salt = salt or random.randbytes(16)  # Random salt for security
        self.counters = [0] * num_counters

    def _hash(self, tx_hash: bytes, index: int) -> int:
        """Compute a hash value for the given transaction and hash function index."""
        # Combine transaction hash, salt, and hash function index.
        combined = tx_hash + self.salt + index.to_bytes(4, byteorder="big")
        hash_value = int(hashlib.sha256(combined).hexdigest(), 16)
        return hash_value % self.num_counters

    @property
    def count_num(self):
        return sum(self.counters) / self.num_hashes

    def add_transaction(self, tx_hash: bytes):
        """Add a transaction to the accumulator."""
        for i in range(self.num_hashes):
            index = self._hash(tx_hash, i)
            self.counters[index] += 1

    def delete_transaction(self, tx_hash: bytes):
        """Delete a transaction from the accumulator."""
        for i in range(self.num_hashes):
            index = self._hash(tx_hash, i)
            self.counters[index] -= 1

    def to_bytes(self) -> bytes:
        """Return the accumulator state as a byte string."""
        # Find the minimum counter value.
        min_counter = min(self.counters)
        # Subtract the minimum from all counters to reduce their size.
        adjusted_counters = [c - min_counter for c in self.counters]
        # Pack the adjusted counters into a byte string.
        state = b""
        for counter in adjusted_counters:
            state += counter.to_bytes(self.counter_size, byteorder="big")
        # Add the minimum counter value to the state.
        state += min_counter.to_bytes(self.counter_size, byteorder="big")
        # Add the salt to the state
        state += self.salt
        return state

    @classmethod
    def from_bytes(
        cls, state: bytes, num_counters: int = DEFAULT_NUM_COUNTERS,
        num_hashes: int = DEFAULT_NUM_HASHES, counter_size: int = DEFAULT_COUNTER_SIZE
    ):
        """Create an accumulator from a byte string."""
        expected_salt_length = 16
        counter_bytes = counter_size * num_counters
        min_counter_start = counter_bytes
        min_counter_end = min_counter_start + counter_size
        salt_start = min_counter_end
        salt_end = len(state)

        if salt_end - salt_start != expected_salt_length:
            raise ValueError(
                f"Salt length is incorrect. Expected {expected_salt_length}, got {salt_end - salt_start}"
            )

        if min_counter_end > len(state):
            raise ValueError("State is too short to contain min_counter and salt.")

        counter_values = []
        for i in range(num_counters):
            start = i * counter_size
            end = start + counter_size
            if end > min_counter_start:
                raise ValueError("State is too short to contain all counters.")
            counter_bytes_i = state[start:end]
            counter_values.append(int.from_bytes(counter_bytes_i, byteorder="big"))

        min_counter = int.from_bytes(
            state[min_counter_start:min_counter_end], byteorder="big"
        )
        # Extract the salt from the end of the state
        salt = state[salt_start:salt_end]
        accumulator = cls(
            num_counters=num_counters,
            num_hashes=num_hashes,
            counter_size=counter_size,
            salt=salt,
        )
        accumulator.counters = [counter + min_counter for counter in counter_values]
        return accumulator
