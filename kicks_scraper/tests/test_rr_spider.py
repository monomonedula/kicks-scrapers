import json
import random
from time import time

import pytest
from scrapy import Request

from test_utils.utils import random_strings_gen, random_string
from kicks_scraper.spiders.runrepeat import total_items_num, rr_requests, limited_urls, \
    PaginatingJsonURL


class ResponseMock:
    def __init__(self, txt):
        self.text = txt


def generate_correct_response(num):
    return ResponseMock(
        json.dumps({'aggregations':
                        {'stats': {'total_count_any_size': num}}})
    )


@pytest.mark.parametrize('num', [1, 12, 423, 54357, 44, 0])
def test_total_items_num(num):
    assert total_items_num(
        generate_correct_response(num)
    ) == num


def test_total_items_num_fail_dict():
    with pytest.raises(KeyError):
        total_items_num(ResponseMock(
            json.dumps({'some': {'other': {'keys': 1344}}})
        ))


@pytest.mark.parametrize('obj', [100, json.dumps({'key': 1234}),
                                 dict(text='some text'), 'a string', ])
def test_total_items_num_fail_response(obj):
    with pytest.raises(AttributeError):
        total_items_num(obj)


def random_urls_gen(amount, rand=None):
    rand = rand or random.Random()
    for i in range(amount):
        yield f'http://{random_string(12, rand)}.{random_string(3, rand)}'


class PaginatingJsonURLMock:
    def __init__(self, url):
        self._url = url

    def url(self):
        return self._url

    def next(self):
        return random_string(40)


def random_urls_pg_json_urls(urls):
    yield from (PaginatingJsonURLMock(url) for url in urls)


@pytest.mark.parametrize('iterable', [[1, 2, 3],
                                      random_strings_gen(10),
                                      list(random_strings_gen(10))])
def test_rr_requests_nonurl_fail(iterable):
    with pytest.raises(AttributeError):
        # noinspection PyTypeChecker
        next(
            rr_requests(
                iterable,
                None
            )
        )


@pytest.mark.parametrize('urls', [random_urls_gen(132),
                                  list(random_urls_gen(0)),
                                  tuple(random_urls_gen(334)),
                                  set(random_urls_gen(267))])
def test_rr_requests_return_type(urls):
    urls = random_urls_pg_json_urls(urls)
    assert all(
        map(
            lambda r: isinstance(r, Request),
            rr_requests(urls, None)
        )
    )


@pytest.mark.parametrize('callback', [lambda x: None,
                                      None,
                                      lambda y: 42])
def test_rr_requests_return_contents(callback):
    urls1, urls2 = get_twin_urls_iterables(100)
    urls1 = map(PaginatingJsonURLMock, urls1)
    for request, url in zip(rr_requests(urls1, callback), urls2):
        assert request.url == url and request.callback == callback


def get_twin_urls_iterables(n=100):
    seed = time()
    urls1 = random_urls_gen(n, random.Random(seed))
    urls2 = random_urls_gen(n, random.Random(seed))
    return urls1, urls2


@pytest.mark.parametrize('start, size, limit, length', [(0, 30, 10, 1),
                                                        (10, 50, 5, 0),
                                                        (0, 40, 41, 2),
                                                        (0, 40, 134, 4),
                                                        (0, 10, 0, 0),
                                                        (0, 40, 40, 1),
                                                        (0, 40, 400, 10)])
def test_limited_urls(start, size, limit, length):
    p_url = PaginatingJsonURL(start, size, 'sometemplate/{from_item}/{size}')
    assert len(list(limited_urls(p_url, limit))) == length


@pytest.mark.parametrize('template, start, size', [('tmp{from_item}/{size}', 10, 3),
                                                   ('random{from_item}words{size}', 0, 30),
                                                   ('blabla{size}blabla{from_item}', 1, 0)])
def pagination_json_url_test(template, start, size):
    pg_url = PaginatingJsonURL(start, size, template)

    first = pg_url.next()
    second = PaginatingJsonURL(start + size, size, template)
    assert first.url() == second.url()


@pytest.mark.parametrize('template, start, size', [('tmp{from_item}/{size}', 10, 3),
                                                   ('random{from_item}words{size}', 0, 30),
                                                   ('blabla{size}blabla{from_item}', 0, 0),
                                                   ('blabla_no_format_placeholders', 0, 50)])
def pagination_json_url_test2(template, start, size):
    nxt = PaginatingJsonURL(start, size, template).next()
    assert nxt.template == template and \
        nxt.start == start + size and \
        nxt.size == size
