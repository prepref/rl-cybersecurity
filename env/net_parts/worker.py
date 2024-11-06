from net_parts.utils.device_type import Device_type
from net_parts.device import device
from net_parts.connection import connection

class worker(device):
    device_type = Device_type.worker

    def __init__(self, device_name:str, packet_processing_speed: int):
        self.packet_processing_speed = packet_processing_speed
        self.device_name = device_name
        self.connections = []

    def add_connection(self, connection: connection):
        self.connections.append(connection)

    def remove_connection(self, connection: connection):
        for conn in self.connections:
            if conn.name == connection.name:
                self.connections.remove(conn)
                conn.__del__()