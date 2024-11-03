import json
from utils.device import device
from utils.connection import connection

class net():

    def __init__(self):
        self.devices= [device]
        self.connections= [connection]

    def add_device(self, device:device):
        self.devices.append(device)

    def add_connection(self, connection: connection):
        self.connections.append(connection)

    def from_configuration(self, path_to_file:str):
        with open(path_to_file) as data:
            temp = json.load(data)
            print(temp)
