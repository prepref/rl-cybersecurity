from utils import generator_network, generator_packages_users

def main():
    # packages_dist = generator_packages_users.Generator('halfnormal', loc=200, scale=1000)

    # packages_samples = packages_dist.draw_samples(size=5)
    # print(packages_samples)

    # packages_dist.visualize(bins=100)

    network = generator_network.Network(4,2,3)
    network.generate_network(topology='ring')
    network.network_to_json()


if __name__ == '__main__':
    main()