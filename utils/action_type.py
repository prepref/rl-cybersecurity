from enum import Enum

class Action_type(Enum):
    SINGLE_TARGET_ACTION = 1
    MULTILPE_TARGET_ACTION = 2

class Action(Enum):
    SERVER_RECIEVE_CURRENT = 0
    SERVER_DROP_CURRENT = 1
    SERVER_BLOCK_CURRENT_ADDRESS = 2
    SERVER_BLOCK_CURRENT_ADDRESS_GROUP = 3
    #SERVER_DROP_SIMULAR = 4
    