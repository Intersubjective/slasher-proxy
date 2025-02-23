from pony.orm import db_session

from slasher_proxy.common.log import LOGGER
from slasher_proxy.common.model import AuxiliaryData

DB_VERSION_KEY = "dbVersion"
CURRENT_DB_VERSION = "20"
NETWORK_NAME_KEY = "network"


def upgrade_db(version: int) -> None:
    # TBD
    LOGGER.error("Upgrade not implemented, exiting.")
    exit(1)


@db_session
def check_db_version(network_name: str) -> None:
    v = AuxiliaryData.get(key=DB_VERSION_KEY)
    version = v.value if v else None
    if version is None:
        # New DB, add current version
        AuxiliaryData(key=DB_VERSION_KEY, value=CURRENT_DB_VERSION)
        AuxiliaryData(key=NETWORK_NAME_KEY, value=network_name)
    else:
        if (
            name_in_db := AuxiliaryData.get(key=NETWORK_NAME_KEY).value
        ) != network_name:
            LOGGER.error(
                "DB network name mismatch. Expected: %s, Actual: %s.",
                network_name,
                name_in_db,
            )
            exit(1)
        if version != CURRENT_DB_VERSION:
            LOGGER.warn(
                "DB version mismatch. Expected: %s, Actual: %s. Starting migration",
                CURRENT_DB_VERSION,
                version,
            )
            upgrade_db(version)
