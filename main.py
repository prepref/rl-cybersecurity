from utils import enviroment, server, message_generator

def main():
    server.start()

    env = enviroment.TrafficEnv()

    message_generator.start()

    print(env.get_state())
    print(env.step(0))

if __name__ == '__main__':
    main()