# model.py
import logging
from datetime import datetime

from pony.orm import (
    Database,
    Optional,
    PrimaryKey,
    Required,
    Set,
    composite_index,
    composite_key,
)

from slasher_proxy.common import C_STATUS_PENDING, T_STATUS_SUBMITTED

db = Database()


class Transaction(db.Entity):
    hash = PrimaryKey(bytes)
    status = Required(int, default=T_STATUS_SUBMITTED)
    created_at = Required(datetime, default=lambda: datetime.now())
    from_address = Required(str)
    nonce = Required(int)
    replaces = Optional(bytes, default=None, nullable=True)
    block_transactions = Set(
        "BlockTransaction", reverse="transaction"
    )  # reverse relation


class Commitment(db.Entity):
    node = Required(str)
    tx_hash = Required(bytes)
    index = Required(int)
    accumulator = Optional(bytes)
    status = Required(int, default=C_STATUS_PENDING)  # changed from str to int
    created_at = Required(datetime, default=lambda: datetime.now())
    composite_key(node, tx_hash)
    composite_index(node, index, tx_hash)


class Block(db.Entity):
    number = PrimaryKey(int)
    hash = Required(bytes, unique=True)
    node_id = Required(str)
    created_at = Required(datetime, default=lambda: datetime.now())
    block_transactions = Set("BlockTransaction", reverse="block")  # reverse relation


class BlockTransaction(db.Entity):
    block = Required(Block, reverse="block_transactions")
    transaction = Required(
        Transaction, reverse="block_transactions"
    )  # must be Required!
    order = Required(int)
    PrimaryKey(block, transaction)


class BlockState(db.Entity):
    block_number = PrimaryKey(int)
    accumulator_state = Optional(bytes)
    offset_index = Required(int, default=0)
    shift_index = Required(int, default=0)


class AuxiliaryData(db.Entity):
    key = PrimaryKey(str)
    value = Optional(str)


class NodeStats(db.Entity):
    node = PrimaryKey(str)
    total_transactions = Required(int, default=0)
    reordered_count = Required(int, default=0)
    censored_count = Required(int, default=0)
    last_updated = Required(datetime, default=lambda: datetime.utcnow())


def init_db(provider="sqlite", filename=":memory:", create_db=True, create_tables=True):
    if not db.provider:
        db.bind(provider=provider, filename=filename, create_db=create_db)
    try:
        db.generate_mapping(create_tables=create_tables)
    except Exception as e:
        logging.error("Error generating mapping: %s", e)
