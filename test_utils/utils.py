from time import time
import random
import string


def random_strings_gen(amount, rand=None):
    rand = rand or random.Random()
    for i in range(amount):
        yield random_string(rand.randint(0, 200), rand)


def random_string(string_length=10, rand=None):
    """Generate a random string of fixed length """
    rand = rand or random.Random(time())
    letters = string.ascii_lowercase
    return ''.join(rand.choice(letters) for i in range(string_length))


class Random:
    def __init__(self, seed):
        self.seed = seed
        self._rand = random.Random(seed)

    def random_string(self, length):
        letters = string.ascii_lowercase
        return ''.join(self._rand.choice(letters) for i in range(length))

    def randint(self, a, b):
        return self._rand.randint(a, b)

    def random_strings(self, amount, length):
        for i in range(amount):
            yield self.random_string(length)

    def random_strings_range(self, amount_range=(1, 100),
                             length_range=(5, 50)):
        for i in range(self.randint(*amount_range)):
            yield self.random_string(self.randint(*length_range))