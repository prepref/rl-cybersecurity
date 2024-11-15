import requests

def generate_request(url, message):
    requests.post(url=url, data=message)