import socket
import string
import random
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

_user_server = None

def send_messages(agent_host, agent_port, host, port, min_intv, max_intv) -> str:
    global _user_server
    symbols = string.ascii_letters+string.digits
    
    while True:
        try:
            _user_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            _user_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            _user_server.bind((host, port))
            _user_server.connect((agent_host,agent_port))
            
            while True:
                is_user = random.random() < 0.35

                if is_user:
                    ip_address = '72.166.25.' + str(random.randint(1,200))
                    message = ''.join(random.choice(symbols) for _ in range(random.randint(1,30)))
                    interval = 2
                else:
                    ip_address = '72.166.25.' + str(random.randint(200,255))
                    message = ''.join(random.choice(symbols) for _ in range(random.randint(1,5)))
                    interval = 1
                # interval = random.randint(min_intv,max_intv)
                message = f'{message}@@{ip_address}@@{is_user}'
                _user_server.sendall(message.encode('utf-8'))
                logging.info(f"{'Пользователь' if is_user else 'Бот'} отправил сообщение на {agent_host}:{agent_port}")
                time.sleep(interval)
                
        except (ConnectionAbortedError, ConnectionResetError, ConnectionRefusedError) as e:
            logging.warning(f"Соединение прервано: {e}. Идет переподключение...")
            if '_user_server' in locals():
                _user_server.close()

        except Exception as e:
            logging.error(f"Неожиданная ошибка: {e}")
            if '_user_server' in locals():
                _user_server.close()
            raise

def start(host='127.0.0.1', port=8070, agent_host='127.0.0.1', agent_port=8090, 
          min_intv=3, max_intv=10):
    send_messages(agent_host=agent_host, agent_port=agent_port, host=host, 
                 port=port, min_intv=min_intv, max_intv=max_intv)



