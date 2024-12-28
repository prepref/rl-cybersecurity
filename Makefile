.PHONY: all clean run_server run_env

all: run_server run_env

run_server:
	tmux new-session -d -s server_session 'python3 ./utils/server.py'

run_env:
	python3 ./utils/enviroment.py

clean:
	rm -rf ./utils/__pycache__/*.pyc