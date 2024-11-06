from net_parts.device import device


class connection():

    def __init__(self, connection_name:str, device1: device, device2: device, bandwidth: int):
        self.name = connection_name

        self.device1 = device1
        device1.add_connection(self)

        self.device2 = device2
        device2.add_connection(self)

        self.bandwidth = bandwidth
        self.isActive = True

    def Disable(self) -> None:
        self.isActive = False

    def Enable(self) -> None:
        self.isActive = True