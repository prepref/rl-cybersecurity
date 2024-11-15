import socket
import logging
import psutil # чтобы тянуть состояние сервера
import threading
# from prometheus_client import start_http_server, Counter, Gauge

#Port for start_http_server = 8000

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# PACKETS_RECEIVED = Counter('packets_received_total', 'Total number of packets received')
# PACKETS_BLOCKED = Counter('packets_blocked_total', 'Total number of packets blocked')
# CPU_USAGE = Gauge('cpu_usage_percent', 'Current CPU usage in percent')
# MEMORY_USAGE = Gauge('memory_usage_percent', 'Current memory usage in percent')

# def update_system_metrics():
#     CPU_USAGE.set(psutil.cpu_percent(interval=1))
#     MEMORY_USAGE.set(psutil.virtual_memory().percent)

def handle_client(conn, addr):
    logging.info(f"Подключение от {addr}")
    while True:
        data = conn.recv(1024)
        if not data:
            break
        # PACKETS_RECEIVED.inc()
        logging.info(f"Получен пакет:\n{data.decode('utf-8')}")
        # update_system_metrics()
    conn.close()

def start(host='127.0.0.1', port=8080):
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