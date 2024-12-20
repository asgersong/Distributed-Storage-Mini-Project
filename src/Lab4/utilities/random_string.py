import random, string

def random_string(length=8):
    """
    Returns a random alphanumeric string of the given length.
    Only lowercase ascii letters and numbers are used.

    :param length: Length of the requested random string
    :return: The random generated string
    """

    return "".join(
        [
            random.SystemRandom().choice(string.ascii_letters + string.digits)
            for n in range(length)
        ]
    )
