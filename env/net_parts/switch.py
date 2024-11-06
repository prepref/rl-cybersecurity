from net_parts.utils.device_type import Device_type
from net_parts.device import device
from net_parts.connection import connection


class switch(device):

    device_type = Device_type.switch

    def __init__(self, device_name:str, memory_limit: int):
        self.memory_limit = memory_limit
        self.device_name = device_name
        self.connections = []

    def add_connection(self, connection: connection):
        self.connections.append(connection)

    def remove_connection(self, connection: connection):
        for conn in self.connections:
            if conn.name == connection.name:
                self.connections.remove(conn)
                conn.__del__()