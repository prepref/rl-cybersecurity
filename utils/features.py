import re
import socket
import ipinfo

import numpy as np

from collections import defaultdict
    
class Features:
    def __init__(self):
        self.user_groups = defaultdict(list)
        self.ip_blocks = defaultdict(int)

    def _get_ip_from_domain(self, domain):
        try: 
            return socket.gethostbyname(domain)
        except socket.gaierror:
            return None
    
    def _get_netmask_from_ip(self, ip_address):
        token = '142af0e70792ef'
        handler = ipinfo.getHandler(token)
        details = handler.getDetails(ip_address)
        netmask = details.asn['route'].split('/')[0]
        return netmask

    def extract(self, message, interval):
        host = re.search(r'Host: (\S+)', message)
        domain = host.group(1)
        ip_address = self._get_ip_from_domain(domain=domain)
        netmask = self._get_netmask_from_ip(ip_address=ip_address)

        self.user_groups[ip_address].append((netmask, interval, message))

        bytes_m = len(message.encode('utf-8'))
        self.ip_blocks[netmask] += bytes_m
        bytes_b = self.ip_blocks[netmask]

        user_intervals = np.array([item[1] for item in self.user_groups[ip_address]])

        ave = np.sum(user_intervals) / ((len(user_intervals) - 1) if len(user_intervals) -1  != 0 else 1)
        dev = (np.sum(user_intervals) - ave) / ((len(user_intervals) - 1) if len(user_intervals) -1  != 0 else 1)
        num_m = len(self.user_groups[ip_address])

        print(f'Domain: {domain}; ip: {ip_address}; mask: {netmask}')

        return np.array([bytes_m, bytes_b, ave, dev, num_m])