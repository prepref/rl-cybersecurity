import json
from net_parts.connection import connection
from net_parts.device import device
from net_parts.switch import switch
from net_parts.worker import worker

class net():

    def __init__(self):
        self.devices= []
        self.connections= []

    def add_device(self, device:device):
        self.devices.append(device)

    def add_connection(self, connection: connection):
        self.connections.append(connection)

    def from_configuration(self, path_to_file:str):
        with open(path_to_file) as data:
            temp = json.load(data)
            print(temp)


if __name__ == '__main__':
    net_1 = net()
    dev1 = switch("1", 20)
    dev2 = worker("2", 5)
    con1 = connection("1", dev1, dev2, 10)
    net_1.add_device(dev1)
    net_1.add_device(dev2)
    net_1.add_connection(con1)
    print(net_1.devices[0].device_name)
    print(net_1.devices[0].connections[0].bandwidth)
