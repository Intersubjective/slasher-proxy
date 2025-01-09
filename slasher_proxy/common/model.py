from pony import orm

from slasher_proxy.common import T_STATUS_SUBMITTED, db


class Transaction(db.Entity):
    hash = orm.PrimaryKey(bytes)
    raw_content = orm.Required(bytes, unique=True)
    status = orm.Required(int, default=T_STATUS_SUBMITTED)


class Block(db.Entity):
    number = orm.PrimaryKey(int)
    hash = orm.Required(bytes, unique=True)
    raw_content = orm.Required(bytes)

class Commitment(db.Entity):
    transaction_hash = orm.PrimaryKey(bytes)
    content = orm.Required(bytes, unique=True)

class AuxiliaryData(db.Entity):
    key = orm.PrimaryKey(str)
    value = orm.Optional(str)

