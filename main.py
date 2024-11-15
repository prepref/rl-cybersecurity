from utils import server, env

def main():
    server.start_http_server(8000)
    server.start()

    e = env.TrafficEnv()

    

if __name__ == '__main__':
    main()