from utils import generator

def main():
    packages_dist = generator.Generator('halfnormal', loc=200, scale=1000)

    packages_samples = packages_dist.draw_samples(size=5)
    print(packages_samples)

    packages_dist.visualize(bins=100)

if __name__ == '__main__':
    main()