from flask import Flask, render_template, request, Response
import threading
import requests
import time
import queue
import logging

app = Flask(__name__)
thread_worker = None
q = queue.Queue()
SWITCHER = True

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def generate_request(queue: queue.Queue):
    while True:
        data = queue.get()
        if data is None:
            break
        url = data["address"]
        message = data["message"]
        delay = data['delay']
        while SWITCHER:
            try:
                requests.post("http://" + url, timeout=1, data=message)
            except requests.exceptions.RequestException as e:
                pass
            time.sleep(int(delay) / 1000)
        queue.task_done()

@app.route("/")
def main():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    global SWITCHER, thread_worker
    SWITCHER = True
    content = request.get_json()
    q.put({"address": content["address"], "message": content["message"], "delay": content["delay"]})
    thread_worker = threading.Thread(target=generate_request, args=(q,))
    thread_worker.start()
    return Response(status=200)

@app.route('/stop', methods=['POST'])
def stop():
    global SWITCHER
    SWITCHER = False
    q.put(None)  # Signal the thread to stop
    logging.info("Sent stop signal to thread worker.")
    if thread_worker and thread_worker.is_alive():
        thread_worker.join()
        logging.info("Thread worker stopped.")
    return Response(status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9800, debug=True)