from typing import Optional

import logging
from datetime import datetime

from pony.orm import Optional as PonyOptional
from pony.orm import PrimaryKey, Required, Set, composite_index, composite_key

from slasher_proxy.common import C_STATUS_PENDING, T_STATUS_SUBMITTED, db

Entity = db.Entity  # Added alias for mypy


class Transaction(Entity):  # type: ignore
    hash: bytes = PrimaryKey(bytes)
    status: int = Required(int, default=T_STATUS_SUBMITTED)
    created_at: datetime = Required(datetime, default=lambda: datetime.now())
    from_address: str = Required(str)
    nonce: int = Required(int)
    replaces: Optional[bytes] = PonyOptional(bytes, default=None, nullable=True)
    block_transactions = Set(
        "BlockTransaction", reverse="transaction"
    )  # reverse relation


class Commitment(Entity):  # type: ignore
    node: str = Required(str)
    tx_hash: bytes = Required(bytes)
    index: int = Required(int)
    accumulator: Optional[bytes] = PonyOptional(bytes)
    status: int = Required(int, default=C_STATUS_PENDING)  # changed from str to int
    created_at: datetime = Required(datetime, default=lambda: datetime.now())
    composite_key(node, tx_hash)
    composite_index(node, index, tx_hash)


class Block(Entity):  # type: ignore
    number: int = PrimaryKey(int)
    hash: bytes = Required(bytes, unique=True)
    node_id: str = Required(str)
    created_at: datetime = Required(datetime, default=lambda: datetime.now())
    block_transactions = Set("BlockTransaction", reverse="block")  # reverse relation


class BlockTransaction(Entity):  # type: ignore
    block = Required(Block, reverse="block_transactions")
    transaction = Required(
        Transaction, reverse="block_transactions"
    )  # must be Required!
    order: int = Required(int)
    PrimaryKey(block, transaction)


class BlockState(Entity):  # type: ignore
    block_number: int = PrimaryKey(int)
    accumulator_state: Optional[bytes] = PonyOptional(bytes)
    offset_index: int = Required(int, default=0)
    shift_index: int = Required(int, default=0)


class AuxiliaryData(Entity):  # type: ignore
    key: str = PrimaryKey(str)
    value: Optional[str] = PonyOptional(str)


class NodeStats(Entity):  # type: ignore
    node: str = PrimaryKey(str)
    total_transactions: int = Required(int, default=0)
    reordered_count: int = Required(int, default=0)
    censored_count: int = Required(int, default=0)
    last_updated: datetime = Required(datetime, default=lambda: datetime.utcnow())


def init_db(
    provider: str = "sqlite",
    filename: str = ":memory:",
    create_db: bool = True,
    create_tables: bool = True,
) -> None:
    if not db.provider:
        db.bind(provider=provider, filename=filename, create_db=create_db)
    try:
        db.generate_mapping(create_tables=create_tables)
    except Exception as e:
        logging.error("Error generating mapping: %s", e)
