from sim_env import HTTPServerEnv
from agent.ddqn_agent import DoubleQAgent
import time
import numpy as np
import matplotlib.pyplot as plt


if __name__=="__main__":
    LEARN_EVERY = 4

    def train_agent(n_episodes=2000):
        print(f"Training a DDQN agent on {n_episodes} episodes.")
        env = HTTPServerEnv(buffer_size=100, load_threshold=0.8, hazard_index=1)
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



    def test_agent(agent, n_episodes=200):
        print(f"Testing a DDQN agent on {n_episodes} episodes.")
        env = HTTPServerEnv(buffer_size=100, load_threshold=0.8, hazard_index=1)

        scores = []
        start = time.time()
        for i in range(n_episodes):
            terminated = False
            score = 0
            state = env.reset()
            while not (terminated):
                action = agent.choose_action(state)
                new_state, reward, terminated, info = env.step(action)
                state = new_state
                score += reward
                
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
                    
        return scores


    # Uncomment to train
#    agent, ed_scores = train_agent(n_episodes=100)
#    agent.is_learning = False
#    test_scores = test_agent(agent)
#    ed_indexes = np.arange(len(ed_scores)).tolist()
#    test_indexes = np.arange(len(test_scores)).tolist()

#    plt.plot(ed_indexes, ed_scores)
#    plt.xlabel("Эпизоды обучения")
#    plt.ylabel("Награды")
#    plt.title("Результаты работы агента в процессе обучения")
#    plt.show(block=True)

#    plt.plot(test_indexes, test_scores)
#    plt.xlabel("Эпизоды тестирования")
#    plt.ylabel("Награды")
#    plt.title("Результаты работы агента в процессе тестирования")
#    plt.show(block=True)