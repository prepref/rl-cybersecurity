from device_type import Device_type
from connection import connection

class device():
    connections = [connection]

    def create_switch(self, device_name:str, memory_limit: int):
        if self.device_type == Device_type.worker:
            return TypeError("This device already set as a worker")

        self.device_type = Device_type.switch
        self.memory_limit = memory_limit
        self.device_name = device_name

    def create_worker(self, device_name:str, packet_processing_speed: int):
        if self.device_type == Device_type.switch:
            return TypeError("This device already set as a switch")
        
        self.device_type = Device_type.worker
        self.packet_processing_speed = packet_processing_speed
        self.device_name = device_name

    def add_connection(self, connection: connection):
        self.connections.append(connection)

    def remove_connection(self, connection):
        for conn in self.connections:
            if conn.name == connection.name:
                self.connections.remove(conn)
                conn.__del__()

