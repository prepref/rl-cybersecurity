import numpy as np

from collections import defaultdict
    
class Features:
    def __init__(self):
        self.user_groups = defaultdict(list)
        self.ip_blocks = defaultdict(int)
    
    def get_netmask_from_ip(self, ip_address):
        ip_parts = ip_address.split('.')
        return '.'.join(ip_parts[:-1])

    def extract(self, message, interval, ip_address):
        if ':' in ip_address:
            ip_address = ip_address.split(':')[0]

        netmask = self.get_netmask_from_ip(ip_address=ip_address)

        self.user_groups[ip_address].append((netmask, interval, message))

        bytes_m = len(message.encode('utf-8'))
        self.ip_blocks[netmask] += bytes_m
        bytes_b = self.ip_blocks[netmask]

        user_intervals = np.array([item[1] for item in self.user_groups[ip_address]])

        ave = np.sum(user_intervals) / ((len(user_intervals) - 1) if len(user_intervals) -1  != 0 else 1)
        dev = (np.sum(user_intervals) - ave) / ((len(user_intervals) - 1) if len(user_intervals) -1  != 0 else 1)
        num_m = len(self.user_groups[ip_address])

        return np.array([bytes_m, bytes_b, ave, dev, num_m])