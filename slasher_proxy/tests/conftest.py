from typing import Generator

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
    db,
    init_db,
)


# Initialize the in-memory database and create all tables once per test session.
@pytest.fixture(scope="session", autouse=True)
def initialize_database() -> None:  # type: ignore
    # Use shared in-memory DB so all threads and the app see the same instance.
    init_db(
        provider="sqlite",
        filename=":memory:?cache=shared",
        create_db=True,
        create_tables=True,
    )
    yield
    # Drop tables at the end of the session, outside any db_session.
    db.drop_all_tables(with_all_data=True)


# Clear the database between tests in the proper order.
@pytest.fixture(autouse=True)
def clear_database() -> Generator[None, None, None]:
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
