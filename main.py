from utils import enviroment
from agent.ddqn_agent import DoubleQAgent
import time
import numpy as np

LEARN_EVERY = 4

def train_agent(n_episodes=2000):
    print(f"Training a DDQN agent on {n_episodes} episodes.")
    env = enviroment.TrafficEnv(mode="simulation")

    agent = DoubleQAgent(observation_space_shape=env.observation_space.shape[0], action_space_n=env.action_space.n, 
                             gamma=0.99, epsilon=1.0, epsilon_dec=0.995, lr=0.001, mem_size=200000, batch_size=128, epsilon_end=0.01)
            
    scores = []
    eps_history = []
    start = time.time()
    for i in range(n_episodes):
        terminated = False
        score = 0
        state = env.reset()
        steps = 0
        while not (terminated):
            env.get_state()
            action = agent.choose_action(state)
            new_state, reward, terminated, info = env.step(action)
            agent.save(state, action, reward, new_state, terminated)
            state = new_state
            if steps > 0 and steps % LEARN_EVERY == 0:
                agent.learn()
            steps += 1
            score += reward
                
        eps_history.append(agent.epsilon)
        scores.append(score)
        avg_score = np.mean(scores[max(0, i-100):(i+1)])

        if (i+1) % 10 == 0 and i > 0:
            # Report expected time to finish the training
            print('Episode {} in {:.2f} min. Expected total time for {} episodes: {:.0f} min. [{:.2f}/{:.2f}]'.format((i+1), 
                                                                                                                        (time.time() - start)/60, 
                                                                                                                        n_episodes, 
                                                                                                                        (((time.time() - start)/i)*n_episodes)/60, 
                                                                                                                        score, 
                                                                                                                        avg_score))
                    
    return agent, scores

def main():
    train_agent()

if __name__ == '__main__':
    main()