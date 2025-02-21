import pytest
from pony.orm import commit, db_session

from slasher_proxy.common.model import (
    AuxiliaryData,
    Block,
    BlockState,
    BlockTransaction,
    Commitment,
    NodeStats,
    Transaction,
    init_db,
)


# Initialize the database once per test session.
@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    init_db()


# Clear the database between tests in the proper order.
@pytest.fixture(autouse=True)
def clear_database():
    # Before each test, remove all data.
    with db_session:
        # Delete child/association tables first.
        BlockTransaction.select().delete(bulk=True)
        Commitment.select().delete(bulk=True)
        BlockState.select().delete(bulk=True)
        # Then delete parent tables.
        Block.select().delete(bulk=True)
        Transaction.select().delete(bulk=True)
        AuxiliaryData.select().delete(bulk=True)
        NodeStats.select().delete(bulk=True)
        commit()
    yield
    # After each test, clear again.
    with db_session:
        BlockTransaction.select().delete(bulk=True)
        Commitment.select().delete(bulk=True)
        BlockState.select().delete(bulk=True)
        Block.select().delete(bulk=True)
        Transaction.select().delete(bulk=True)
        AuxiliaryData.select().delete(bulk=True)
        NodeStats.select().delete(bulk=True)
        commit()
