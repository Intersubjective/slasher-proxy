from pydantic import PostgresDsn

from slasher_proxy.common import db
from slasher_proxy.common.log import LOGGER
from slasher_proxy.common.upgrade import check_db_version


class GetOrInsertMixin:
    @classmethod
    def get_or_insert(cls, **kwargs):
        return cls.get(**kwargs) or cls(**kwargs)



def start_db(dsn:PostgresDsn, network_name=None):
    db.bind(provider="postgres", dsn=str(dsn))
    db.generate_mapping(create_tables=True)
    check_db_version(network_name)
    LOGGER.info("database is successfully started up")
