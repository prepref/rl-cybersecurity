from sim_env import HTTPServerEnv

env = HTTPServerEnv(buffer_size=100, load_threshold=0.8, hazard_index=1)
obs = env.reset()
for _ in range(1000):
    action = env.action_space.sample()  # Случайное действие
    obs, reward, done, info = env.step(action)
    print(obs, reward)
    if done:
        obs = env.reset()