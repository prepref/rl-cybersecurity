from flask import Flask, render_template, request, Response
import generator
import threading
import requests
import time
import queue
app = Flask(__name__)
thread_worker = None
q = queue.Queue()
delay = 1
SWITCHER = True
def generate_request(queue: queue.Queue):
    data = queue.get()
    url = data["address"]
    message = data["message"]
    delay = data['delay']
    global SWITCHER
    while SWITCHER:
        try:
            requests.post("http://"+url,timeout=0.0000000001, data=message)
            print('Request sended.')
        except Exception: 
            pass
        time.sleep(int(delay) / 1000)
        
with app.app_context():
    thread_worker = threading.Thread(target=generate_request, args=(q,))

@app.route("/")
def main():
    return render_template('index.html')

@app.route('/start', methods=['POST'])
def start():
    global SWITCHER, args, thread_worker
    SWITCHER = True
    content = request.get_json()
    q.put({"address": content["address"],"message": content["message"], "delay": content["delay"]})
    thread_worker = threading.Thread(target=generate_request, args=(q,))
    thread_worker.start()
    return Response(status=200)

@app.route('/stop', methods=['POST'])
def stop():
    global SWITCHER
    SWITCHER = False
    thread_worker.join()
    return Response(status=200)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9800, debug=True)