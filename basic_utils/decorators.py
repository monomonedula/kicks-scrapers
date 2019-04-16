from functools import wraps


def text_lower(func):
    @wraps(func)
    def decor(*args, **kwargs):
        return func(*args, **kwargs).lower()
    return decor


def text_spaces_del(func):
    @wraps(func)
    def decor(*args, **kwargs):
        return ' '.join(func(*args, **kwargs).split())
    return decor


def size_value_format_check(func):
    @wraps(func)
    def decor(s):
        res = func(s)
        try:
            float(res)
        except ValueError:
            raise ValueError('Wrong size value format: "{}"'.format(s))
        return res

    return decor
