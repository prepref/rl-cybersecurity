import socket
import logging
import psutil # чтобы тянуть состояние сервера
import threading
from prometheus_client import Gauge

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

CPU_USAGE = Gauge('cpu_usage_percent', 'Current CPU usage in percent')
MEMORY_USAGE = Gauge('memory_usage_percent', 'Current memory usage in percent')

def update_system_metrics():
    CPU_USAGE.set(psutil.cpu_percent(interval=1))
    MEMORY_USAGE.set(psutil.virtual_memory().percent)

def handle_client(conn, addr):
    logging.info(f"Подключение от {addr}")
    while True:
        data = conn.recv(1024)
        if not data:
            break

        logging.info(f"Получен пакет:\n{data.decode('utf-8')}")
        update_system_metrics()

        if data.decode('utf-8').strip() == 'get state':
            state = f'{psutil.cpu_percent(interval=1)} {psutil.virtual_memory().percent}'

            conn.sendall(str(state).encode('utf-8'))

    conn.close()

def start(host='127.0.0.1', port=8080, memory_limit = 512 * 1024 * 1024):
    process = psutil.Process()
    process.rlimit(psutil.RLIMIT_AS, (memory_limit, memory_limit))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        logging.info(f"Сервер запущен на {host}:{port}")

        while True:
            conn, addr = s.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

if __name__ == "__main__":
    start()