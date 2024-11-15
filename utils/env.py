import socket
import logging
import features
import time

import numpy as np
import gymnasium as gym

from gymnasium import spaces
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class TrafficEnv(gym.Env):
    def __init__(self, proxy_host='127.0.0.1', proxy_port=8090, server_host='127.0.0.1', server_port=8080, mode='train'):
        super(TrafficEnv).__init__()
        self.mode = mode

        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(5,), dtype=np.float32)
        self.action_space = spaces.Discrete(6)  # предварительно

        self.state = np.zeros(5, dtype=np.float32)
        self.time_step = 0
        self.max_time_step = 1000

        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.server_host = server_host
        self.server_port = server_port

        self.features = features.Features()
        self.proxy_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy_s.bind((self.proxy_host, self.proxy_port))
        self.proxy_s.listen()

        self.current_data = None
        self.last_message_time = defaultdict(int)

        logging.info(f"Прокси-сервер запущен на {self.proxy_host}:{self.proxy_port}")

    def get_state(self):
        conn, addr = self.proxy_s.accept()
        with conn:
            logging.info(f'Подключение от {addr}')
            data = conn.recv(1024)
            current_time = time.time() 
            if data:
                self.current_data = data
                self.last_message_time[addr[0]] += current_time - self.last_message_time[addr[0]] 
                self.state = self.features.extract(data.decode('utf-8'), self.last_message_time[addr[0]])
            else:
                self.state = None
        
        return self.state

    def reset(self):
        self.state = np.zeros(5, dtype=np.float32)
        self.time_step = 0
        return self.state

    def step(self, action):
        self.time_step += 1

        if action == 0:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_s:
                server_s.connect((self.server_host, self.server_port))
                server_s.sendall(self.current_data)
                logging.info(f'Данные отправлены на сервер {self.server_host}:{self.server_port}')

        reward = 1  # определить функцию, которая бы принимала вектор состояния и выдавала число
        done = self.time_step >= self.max_time_step
        info = {}

        return None, reward, done, info
    
e = TrafficEnv()

for i in range(10):
    print(e.get_state())
    print(e.step(0))