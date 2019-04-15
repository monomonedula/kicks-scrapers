import re


def only_digits(text):
    return re.sub("[^0-9]", "", text)
