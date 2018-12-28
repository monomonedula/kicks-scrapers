from functools import wraps
from threading import Thread


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


def text_smart_spaces_del(func):
    rare_symbols = ('~', '@', '`', '#', '%', '^', '&', '*', '+', '/', '$', ':',)

    @wraps(func)
    def decor(*args, **kwargs):
        res = func(*args, **kwargs)
        for s in rare_symbols:
            if s not in res:
                res = res.replace('\n', s )
                res = ' '.join(res.split())
                return res.replace(s, '\n')
        else:
            raise ValueError('Cannot find symbol to temporary replace new line symbol')
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


def non_blocking(func):
    @wraps(func)
    def decor(*args, **kwargs):
        t = Thread(target=func, args=args, kwargs=kwargs)
        t.start()
    return decor
