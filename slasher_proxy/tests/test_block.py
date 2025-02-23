# test_block.py

# Import the module that initializes Pony ORM.
from typing import Generator

import pytest
from pony.orm import commit, db_session

from slasher_proxy.common import model
from slasher_proxy.common.model import Block


@pytest.fixture(scope="session", autouse=True)
def setup_db() -> Generator[None, None, None]:
    model.init_db()
    yield
    # Optionally disconnect or cleanup here


# Now you can safely use your entities.
def create_test_block(block_number: int, node_id: str) -> Block:
    with db_session:
        block = model.Block(
            number=block_number,
            hash=b"block" + str(block_number).encode(),
            node_id=node_id,
        )
        commit()
        return block


def test_block_creation() -> None:
    # Create a block using the helper function.
    block = create_test_block(1, "nodeA")

    # Retrieve it from the database and check its properties.
    with db_session:
        retrieved = model.Block.get(number=1)
        assert retrieved is not None
        assert retrieved.hash == b"block1"
        assert retrieved.node_id == "nodeA"
