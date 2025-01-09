from pony import orm

T_STATUS_SUBMITTED = 0
T_STATUS_IN_BLOCK = 1
T_STATUS_ERROR = 2
T_STATUS_REORDERED = 3

# PonyORM set up
db = orm.Database()
