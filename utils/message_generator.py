import socket
import string
import random
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

_user_server = None

def send_messages(agent_host, agent_port, host, port, nums_messages, is_user,
                  min_intv, max_intv) -> str:
    global _user_server

    symbols = string.ascii_letters+string.digits
    for _ in range(nums_messages):
        if is_user:
            ip_address = '72.166.25.' + str(random.randint(1,200))
        else:
            ip_address = '72.166.25.' + str(random.randint(200,255))

        interval = random.randint(min_intv,max_intv)
        message = ''.join(random.choice(symbols) for _ in range(random.randint(1,30)))
        message = f'{message}@@{ip_address}@@{is_user}'
        _user_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _user_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR)
        _user_server.bind((host, port))
        _user_server.connect((agent_host,agent_port))
        _user_server.sendall(message.encode('utf-8'))
        logging.info(f"Пользователь отправил сообщение на {agent_host}:{agent_port}")
        time.sleep(interval)
    
    _user_server.close()

def start(host='127.0.0.1',port=8070 ,agent_host='127.0.0.1', agent_port=8090, nums_messages=100, is_user=True,
          min_intv=3, max_intv=10):
    send_messages(agent_host, agent_port, host, port, nums_messages, is_user, min_intv, max_intv)

start(min_intv=1, max_intv=1)



