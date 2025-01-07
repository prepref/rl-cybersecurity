import socket
import logging
import time
import queue

import numpy as np
import gymnasium as gym

from gymnasium import spaces
from collections import defaultdict

from utils import features
from utils.action_type import Action_type, Action

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class TrafficEnv(gym.Env):
    def __init__(self, proxy_host='127.0.0.1', proxy_port=8090,
                    server_host='127.0.0.1', server_port=8080,
                    mode='train', load_threshold=0.75, hazard_index=1):

        super(TrafficEnv).__init__()
        self.mode = mode

        self.load_threshold = load_threshold
        self.hazard_index = hazard_index
        self.request_buffer = [] # элемент массива (request, bool), true если пакет от нормального пользователя
        self.blocked_ips = set()
        self.blocked_ip_blocks = set()

        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(7,), dtype=np.float32)
        self.action_space = spaces.Discrete(4)

        self.state_data = np.zeros(5, dtype=np.float32)
        self.state_server = np.zeros(2, dtype=np.float32)
        self.time_step = 0
        self.max_time_step = 100

        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.server_host = server_host
        self.server_port = server_port

        self.features = features.Features()

        self.proxy_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy_server.bind((self.proxy_host, self.proxy_port))
        self.proxy_server.listen()

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.connect((self.server_host, self.server_port))

        self.current_data = None
        self.last_message_time = defaultdict(int)

        logging.info(f"Прокси-сервер запущен на {self.proxy_host}:{self.proxy_port}")
        logging.info(f"Агент подключен к серверу по адресу {self.server_host}:{self.server_port}")


    def get_state(self):
        conn, addr = self.proxy_server.accept()

        with conn:
            logging.info(f'Подключение от {addr}')
            data = conn.recv(1024).decode('utf-8')
            current_time = time.time()
            if self.mode=='simulation':
                data, addr, is_user = data.split('@@')
            
            if data:
                self.current_data = data
                self.last_message_time[addr[0]] += current_time - self.last_message_time[addr[0]] 
                self.state_data = self.features.extract(data, self.last_message_time[addr[0]], addr[0])
            else:
                self.state_data = np.zeros(5, np.float32)
            
        self.server.sendall(b'get state for features')
        data = self.server.recv(1024)
        cpu_usage, memory_usage = data.decode('utf-8').split(' ')
        self.state_server = np.array([np.float32(cpu_usage), np.float32(memory_usage)])

        self.request_buffer.append((addr,np.hstack((self.state_data, self.state_server)), bool(is_user)))
        
        return None


    def reset(self):
        self.state_data = np.zeros(5, dtype=np.float32)
        self.state_server = np.zeros(2, dtype=np.float32)
        self.time_step = 0

        for _ in range(100):
            v = self.get_state()
        
        print(f'Shape of request_buffer: {len(self.request_buffer)}')

        return self.request_buffer[0][1]
    

    def step(self, action):
        self.time_step += 1
        
        addr,_,is_user = self.request_buffer.pop(0)
        
        if action == Action.SERVER_RECIEVE_CURRENT.value:
            self.server.sendall(self.current_data)
            logging.info(f'Данные отправлены на сервер {self.server_host}:{self.server_port}')

        elif action == Action.SERVER_DROP_CURRENT.value:
            pass

        elif action == Action.SERVER_BLOCK_CURRENT_ADDRESS.value:
            self.blocked_ips.add(addr)

        elif action == Action.SERVER_BLOCK_CURRENT_ADDRESS_GROUP.value:
            request_source_block = self.features.get_netmask_from_ip(addr)
            self.blocked_ip_blocks.add(request_source_block)

        reward = self.get_reward(action, addr, is_user)
        state = self.request_buffer[0][1]
        done = self.time_step >= self.max_time_step
        info = {}
        

        return state, reward, done, info


    def get_server_usage(self):
        self.server.sendall(b'get server usage')
        data = self.server.recv(1024)
        cpu_usage, memory_usage, = data.decode('utf-8').split(' ')

        return np.float32(cpu_usage)/100, np.float32(memory_usage)/100
    
    @staticmethod
    def get_action_type(action):
        if action == Action.SERVER_BLOCK_CURRENT_ADDRESS_GROUP.value:
            return Action_type.MULTILPE_TARGET_ACTION.value
        else:
            return Action_type.SINGLE_TARGET_ACTION.value

    def get_reward(self, action, addr, is_user):
        cpu_usage, memory_usage = self.get_server_usage()
        max_load = max(cpu_usage, memory_usage)
        is_heavy_loaded = max_load >= self.load_threshold
        
        action_type = self.get_action_type(action)
        reward = 0

        if is_heavy_loaded:
            if action_type == Action_type.SINGLE_TARGET_ACTION.value:
                if is_user == True and action == Action.SERVER_RECIEVE_CURRENT.value: #True negative
                    return reward
                
                elif is_user == True and (action == Action.SERVER_DROP_CURRENT.value or action == Action.SERVER_BLOCK_CURRENT_ADDRESS.value): #False Positive
                    reward = -2/(max_load / self.load_threshold * self.hazard_index)
                    return reward
                
                elif is_user == False and action == Action.SERVER_RECIEVE_CURRENT.value: #False Negative
                    reward = -(max_load / self.load_threshold * self.hazard_index)
                    return reward
                
                elif is_user == False and (action == Action.SERVER_DROP_CURRENT.value or action == Action.SERVER_BLOCK_CURRENT_ADDRESS.value): #True Positive
                    reward = max_load / self.load_threshold * self.hazard_index
                    return reward
                
                else:
                    return ValueError(f"Uncnown action: {action}")
                
            elif action_type == Action_type.MULTILPE_TARGET_ACTION.value:
                if action == Action.SERVER_BLOCK_CURRENT_ADDRESS_GROUP.value:
                    fp, tp = 0, 0
                    target_adress_group = self.features.get_netmask_from_ip(addr)
                    for i in range(1, len(self.request_buffer)):
                        if self.features.get_netmask_from_ip(self.request_buffer[i][0]) == target_adress_group:
                            if self.request_buffer[i][2] == True:
                                fp+=1

                            else:
                                tp+=1
                    
                    reward = (max_load / self.load_threshold * self.hazard_index) * tp - (2 / (max_load / self.load_threshold * self.hazard_index) * fp)
                    return reward

                else:
                    return ValueError(f"Uncnown action: {action}")
        
        else:
            if action_type == Action_type.SINGLE_TARGET_ACTION.value:
                if is_user == True and action == Action.SERVER_RECIEVE_CURRENT.value: #True negative
                    return reward
                
                elif is_user == True and (action == Action.SERVER_DROP_CURRENT.value or action == Action.SERVER_BLOCK_CURRENT_ADDRESS.value): #False Positive
                    reward = -2
                    return reward
                
                elif is_user == False and action == Action.SERVER_RECIEVE_CURRENT.value: #False Negative
                    reward = -1
                    return reward
                
                elif is_user == False and (action == Action.SERVER_DROP_CURRENT.value or action == Action.SERVER_BLOCK_CURRENT_ADDRESS.value): #True Positive
                    reward = 1
                    return reward
                
                else:
                    return ValueError(f"Uncnown action: {action}")
                
            elif action_type == Action_type.MULTILPE_TARGET_ACTION.value:
                if action == Action.SERVER_BLOCK_CURRENT_ADDRESS_GROUP.value:
                    fp, tp = 0, 0
                    target_adress_group = self.features.get_netmask_from_ip(addr)
                    for i in range(1, len(self.request_buffer)):
                        if self.features.get_netmask_from_ip(self.request_buffer[i][0]) == target_adress_group:
                            if self.request_buffer[i][2] == True:
                                fp+=1

                            else:
                                tp+=1
                    
                    reward = tp - 2 * fp
                    return reward

                else:
                    return ValueError(f"Uncnown action: {action}")
                