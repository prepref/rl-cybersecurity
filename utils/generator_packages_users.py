import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import halfnorm, expon, uniform, gamma

class Generator:
    def __init__(self, distribution_name, **kwargs):
        """
        Initialize the distribution generator.

        :param distribution_name: Name of the distribution ('halfnormal', 'exponential', 'uniform', 'gamma').
        :param kwargs: Parameters of the distribution. For detailed parameters, refer to the `scipy.stats` documentation.
        """
        self.distribution_name = distribution_name
        self.distribution_params = kwargs

        if self.distribution_name == 'halfnormal':
            self.distribution = halfnorm(**self.distribution_params)
        elif self.distribution_name == 'exponential':
            self.distribution = expon(**self.distribution_params)
        elif self.distribution_name == 'uniform':
            self.distribution = uniform(**self.distribution_params)
        elif self.distribution_name == 'gamma':
            self.distribution = gamma(**self.distribution_params)
        else:
            raise ValueError(f"Unsupported distribution: {self.distribution_name}")

    def generate(self, size=1):
        """
        Generate random numbers from the selected distribution.

        :param size: Number of numbers to generate (default is 1).
        :return: Generated numbers.
        """
        return self.distribution.rvs(size=size)

    def visualize(self, size=1000, bins=30):
        """
        Visualize the distribution.

        :param size: Number of numbers to generate for visualization (default is 1000).
        :param bins: Number of bins for the histogram (default is 30).
        """
        data = self.generate(size=size)
        plt.hist(data, bins=bins, density=True, alpha=0.6, color='g')
        plt.title(f"{self.distribution_name.capitalize()} distribution")
        plt.xlabel("Value")
        plt.ylabel("Probability Density")

        xmin, xmax = plt.xlim()
        x = np.linspace(xmin, xmax, size)
        p = self.distribution.pdf(x)
        plt.plot(x, p, 'k', linewidth=2)

        plt.show()

    def draw_samples(self, size):
        """
        Draw random samples from the selected distribution.

        :param size: Number of samples to draw.
        :return: List of generated samples.
        """
        return [int(abs(num)) for num in self.generate(size)]