from pony.orm import db_session

from slasher_proxy.common.log import LOGGER
from slasher_proxy.common.model import Block


def check_block(notification_from_postgres):
    num_block = int(notification_from_postgres)
    LOGGER.info(f"Block {num_block} notification received")
    with db_session:
        block = Block.get(number=num_block)
    if block is None:
        LOGGER.warning(f"Block {num_block} not found in the database")
        return
    LOGGER.info(f"Block {num_block} hash {block.hash.hex()}")
    # Add some processing logic here, e.g., validate block, etc.
