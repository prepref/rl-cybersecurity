import socket
import logging
import features
import time
import pickle

import numpy as np
import gymnasium as gym

from sklearn.cluster import KMeans
from gymnasium import spaces
from collections import defaultdict
from action_type import Action_type, Action

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def get_action_type(action):
    if action == Action.SERVER_BLOCK_CURRENT_ADDRESS_GROUP:
        return Action_type.MULTILPE_TARGET_ACTION
    else:
        return Action_type.SINGLE_TARGET_ACTION


class TrafficEnv(gym.Env):
    def __init__(self, proxy_host='127.0.0.1', proxy_port=8090,
                    server_host='127.0.0.1', server_port=8080,
                    mode='train', load_threshold=0.75, hazard_index=1):

        super(TrafficEnv).__init__()
        self.mode = mode

        self.load_threshold = load_threshold
        self.hazard_index = hazard_index
        self.request_buffer =[] # элемент массива (request, bool), true если пакет от нормального пользователя
        self.blocked_ips = set()
        self.blocked_ip_blocks = set()

        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(7,), dtype=np.float32)
        self.action_space = spaces.Discrete(4)

        self.state_data = np.zeros(5, dtype=np.float32)
        self.state_server = np.zeros(2, dtype=np.float32)
        self.time_step = 0
        self.max_time_step = 1000

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
            data = conn.recv(1024)
            current_time = time.time() 
            if data:
                self.current_data = data
                self.last_message_time[addr[0]] += current_time - self.last_message_time[addr[0]] 
                self.state_data = self.features.extract(data.decode('utf-8'), self.last_message_time[addr[0]], addr[0])
            else:
                self.state_data = np.zeros(5, np.float32)
            
        self.server.sendall(b'get state for features')
        data = self.server.recv(1024)
        cpu_usage, memory_usage = data.decode('utf-8').split(' ')
        self.state_server = np.array([np.float32(cpu_usage), np.float32(memory_usage)])
        
        return np.hstack((self.state_data, self.state_server))


    def reset(self):
        self.state_data = np.zeros(5, dtype=np.float32)
        self.state_server = np.zeros(2, dtype=np.float32)
        self.time_step = 0
        return np.hstack((self.state_data, self.state_server))
    

    def step(self, action):
        self.time_step += 1
        print(self.current_data)
        if action == Action.SERVER_RECIEVE_CURRENT:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_s:
                server_s.connect((self.server_host, self.server_port))
                server_s.sendall(self.current_data)
                logging.info(f'Данные отправлены на сервер {self.server_host}:{self.server_port}')

        elif action == Action.SERVER_DROP_CURRENT:
            pass #возможно стоит заменить на возврат ошибки

        elif action == Action.SERVER_BLOCK_CURRENT_ADDRESS:
            self.blocked_ips.add(request_source) #Нужно прокинуть адресс текущего запроса

        elif action == Action.SERVER_BLOCK_CURRENT_ADDRESS_GROUP:
            request_source_block = #добавить получение номера группы
            self.blocked_ip_blocks.add(request_source_block)

        reward = self.get_reward(action)
        state = #Добавить получение нового состояния
        done = self.time_step >= self.max_time_step
        info = {}
        

        return state, reward, done, info


    def get_server_usage(self):
        self.server.sendall(b'get server usage')
        data = self.server.recv(1024)
        cpu_usage, memory_usage, = data.decode('utf-8').split(' ')

        return cpu_usage/100, memory_usage/100


    def get_reward(self, action):
        cpu_usage, memory_usage = self.get_server_usage()
        max_load = max(cpu_usage, memory_usage)
        is_heavy_loaded = max_load >= self.load_threshold
        
        action_type = get_action_type(action)
        reward = 0
        
        if is_heavy_loaded:
            if action_type == Action_type.SINGLE_REQUEST_ACTION:
                if self.request_buffer[0][1] == True and action == Action.SERVER_RECIEVE_CURRENT: #True negative
                    return reward
                
                elif self.request_buffer[0][1] == True and (action == Action.SERVER_DROP_CURRENT or action == Action.SERVER_BLOCK_CURRENT_ADDRESS): #False Positive
                    reward = -2/(max_load / self.load_threshold * self.hazard_index)
                    return reward
                
                elif self.request_buffer[0][1] == False and action == Action.SERVER_RECIEVE_CURRENT: #False Negative
                    reward = -(max_load / self.load_threshold * self.hazard_index)
                    return reward
                
                elif self.request_buffer[0][1] == False and (action == Action.SERVER_DROP_CURRENT or action == Action.SERVER_BLOCK_CURRENT_ADDRESS): #True Positive
                    reward = max_load / self.load_threshold * self.hazard_index
                    return reward
                
                else:
                    return ValueError(f"Uncnown action: {action}")
                
            elif action_type == Action_type.MULTILPE_TARGET_ACTION:
                if action == Action.SERVER_BLOCK_CURRENT_ADDRESS_GROUP:
                    fp, tp = 0, 0
                    target_adress_group = self.request_buffer[0][0].address_group
                    for i in range(1, len(self.request_buffer)):
                        if self.request_buffer[i][0].address_group == target_adress_group:
                            if self.request_buffer[i][1] == True:
                                fp+=1

                            else:
                                tp+=1
                    
                    reward = (max_load / self.load_threshold * self.hazard_index) * tp - (2 / (max_load / self.load_threshold * self.hazard_index) * fp)
                    return reward

                else:
                    return ValueError(f"Uncnown action: {action}")
        
        else:
            if action_type == Action_type.SINGLE_REQUEST_ACTION:
                if self.request_buffer[0][1] == True and action == Action.SERVER_RECIEVE_CURRENT: #True negative
                    return reward
                
                elif self.request_buffer[0][1] == True and (action == Action.SERVER_DROP_CURRENT or action == Action.SERVER_BLOCK_CURRENT_ADDRESS): #False Positive
                    reward = -2
                    return reward
                
                elif self.request_buffer[0][1] == False and action == Action.SERVER_RECIEVE_CURRENT: #False Negative
                    reward = -1
                    return reward
                
                elif self.request_buffer[0][1] == False and (action == Action.SERVER_DROP_CURRENT or action == Action.SERVER_BLOCK_CURRENT_ADDRESS): #True Positive
                    reward = 1
                    return reward
                
                else:
                    return ValueError(f"Uncnown action: {action}")
                
            elif action_type == Action_type.MULTILPE_TARGET_ACTION:
                if action == Action.SERVER_BLOCK_CURRENT_ADDRESS_GROUP:
                    fp, tp = 0, 0
                    target_adress_group = self.request_buffer[0][0].address_group
                    for i in range(1, len(self.request_buffer)):
                        if self.request_buffer[i][0].address_group == target_adress_group:
                            if self.request_buffer[i][1] == True:
                                fp+=1

                            else:
                                tp+=1
                    
                    reward = tp - 2 * fp
                    return reward

                else:
                    return ValueError(f"Uncnown action: {action}")

e = TrafficEnv()

for i in range(10):
    print(e.get_state())
    print(e.step(0))