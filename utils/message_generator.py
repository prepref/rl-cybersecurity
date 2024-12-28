import socket
import string
import random
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

_user_server = None

def send_messages(agent_host, agent_port, host, port, nums_messages) -> str:
    global _user_server

    symbols = string.ascii_letters+string.digits
    for _ in range(nums_messages):
        ip_address = '72.166.25.' + str(random.randint(1,255))
        interval = random.randint(1,2)
        message = ''.join(random.choice(symbols) for _ in range(random.randint(1,30)))
        message = f'{message}-{ip_address}'
        _user_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _user_server.bind((host, port))
        _user_server.connect((agent_host,agent_port))
        _user_server.sendall(message.encode('utf-8'))
        logging.info(f"Пользователь отправил сообщение на {agent_host}:{agent_port}")
        time.sleep(interval)

def start(host='127.0.0.1',port=8070 ,agent_host='127.0.0.1', agent_port=8090, nums_messages=100):
    send_messages(agent_host, agent_port, host, port, nums_messages)

start()



