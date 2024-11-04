from typing import List, Dict
from dataclasses import dataclass

import json
import random

@dataclass
class NetworkDevice:
    name: str
    device_type: str
    ip_addresses: List[str]
    ports: List[str]
    connections: Dict[str, int] = None

    def __post_init__(self):
        if len(self.ip_addresses) != len(self.ports):
            raise ValueError
        else:
            self.ports_and_ip = list(zip(self.ports,self.ip_addresses))
        
    def __str__(self):
        return f'{self.device_type}: {self.name}, Ports: {self.ports_and_ip}\n-----'
    
    def to_json(self):
        return {
            'name': self.name,
            'device_type': self.device_type,
            'ports': {pair[0]: pair[1] for pair in self.ports_and_ip},
            'connections': self.connections
        }

@dataclass
class Network:
    num_routers: int
    num_switches: int
    num_servers: int

    def __post_init__(self):
        self.routers_ids = list(range(self.num_routers))
        self.switches_ids = list(range(self.num_routers, self.num_routers + self.num_switches))
        self.servers_ids = list(range(self.num_routers + self.num_switches, self.num_routers + self.num_switches + self.num_servers))
        self.used_ips = set()

    def _get_random_ip(self, count: int):
        ip_addresses = []
        while len(ip_addresses) < count:
            ip = f'10.0.0.{random.randint(0,255)}'
            if ip not in self.used_ips:
                self.used_ips.add(ip)
                ip_addresses.append(ip)

        return ip_addresses

    def _generate_devices(self):
        routers = []
        switches = []
        servers = []

        for id in self.routers_ids:
            routers.append(
                (id, NetworkDevice(
                    name = f'Router{id}',
                    device_type = 'router',
                    ip_addresses = self._get_random_ip(self.num_routers),
                    ports = [f'port{i}' for i in range(self.num_routers)]
                ))
            )
        
        for id in self.switches_ids:
            switches.append(
                (id, NetworkDevice(
                    name = f'Switch{id}',
                    device_type = 'switch',
                    ip_addresses = self._get_random_ip(self.num_switches),
                    ports = [f'port{i}' for i in range(self.num_switches)]
                ))
            )
        
        for id in self.servers_ids:
            servers.append(
                (id, NetworkDevice(
                    name = f'Server{id}',
                    device_type = 'server',
                    ip_addresses = self._get_random_ip(self.num_servers),
                    ports = [f'port{i}' for i in range(self.num_servers)]
                ))
            )
        
        return (routers, switches, servers)
    
    def generate_network(self, topology: str):

        self.routers, self.switches, self.servers = self._generate_devices()
        
        if topology == 'ring':
            for i in range(len(self.routers)):
                self.routers[i][1].connections = {
                    f'{self.routers[i][1].ports[0]}': self.routers[(i + 1) % len(self.routers)][0],
                    f'{self.routers[i][1].ports[1]}': self.routers[(i - 1) % len(self.routers)][0]
                }

            for i, switch in enumerate(self.switches):
                switch[1].connections = {f'{switch[1].ports[0]}': self.routers[i % len(self.routers)][0]}

            for i, server in enumerate(self.servers):
                if i < self.num_servers - 2:
                    server[1].connections = {f'{server[1].ports[0]}': self.switches[i % len(self.switches)][0]}
    
    def network_to_json(self):
        network_data = {
            'devices_id': {
                device[0]: device[1].to_json() for device in self.routers + self.switches + self.servers
            }
        }

        with open('network.json', 'w') as file:
            json.dump(network_data, file, indent=4)