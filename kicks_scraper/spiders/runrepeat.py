import json
import re
from typing import Iterable, Callable
# from urllib.parse import urlparse

import scrapy

from ..items import RunRepeatItem


def total_items_num(response):
    total_items = response.xpath('/html/body/div[2]'
                                 '/div/div/div[1]/header/h1/text()').get()
    total_items = re.sub(r'\d', '', total_items)
    return int(total_items)


def rr_requests(urls: Iterable['PaginatingURL'], callback: Callable):
    for p_url in urls:
        yield scrapy.Request(url=p_url.url(),
                             callback=callback)


def limited_urls(initial_url: 'PaginatingURL', limit: int):
    p_url = initial_url
    while p_url.start < limit:
        yield p_url
        p_url = p_url.next()


class PaginatingURL:
    def __init__(self, start: int, size: int, template: str):
        self.template = template
        self.start = start
        self.size = size

    def url(self):
        return self.template.format(from_item=self.start,
                                    size=self.size)

    def next(self):
        return self.__class__(start=self.start + self.size,
                              size=self.size,
                              template=self.template)


class RRSpider(scrapy.Spider):
    name = 'runrepeat'

    user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0'
    # user_agent = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'

    start_urls = [
        'https://runrepeat.com/ranking/rankings-of-sneakers',

        # 'https://runrepeat.com/ranking/rankings-of-running-shoes',
        # 'https://runrepeat.com/ranking/rankings-of-hiking-boots',
        # 'https://runrepeat.com/ranking/rankings-of-hiking-shoes',
        # 'https://runrepeat.com/ranking/rankings-of-hiking-sandals',
        # 'https://runrepeat.com/ranking/rankings-of-mountaineering-boots',
        # 'https://runrepeat.com/ranking/rankings-of-training-shoes',
        # 'https://runrepeat.com/best-basketball-shoes',
        # 'https://runrepeat.com/ranking/rankings-of-football-boots',
    ]

    templates = {
        'sneakers': 'https://runrepeat.com/get-documents?'
                    'from={from_item}&size={size}&orderBy=score&order=desc&r=1564648578712&filter'
                    '%5B%5D=410&filter%5B%5D=6254&filter%5B%5D=3591&c_id=3&f_id=4',
    }

    def start_requests(self):
        for url, category in self.start_urls:
            meta = {'category': category}
            yield scrapy.Request(url=url,
                                 callback=self.parse,
                                 meta=meta)

    def parse_initial(self, response):
        total_items = total_items_num(response)
        category = response.meta['category']
        template = self.templates[category]

        yield from rr_requests(
            urls=limited_urls(
                initial_url=PaginatingURL(0, 30, template),
                limit=total_items
            ),
            callback=self.parse_json,
        )

    def parse_json(self, response):
        data = json.loads(response.text)
        for item in data:
            yield RunRepeatItem.from_dict(item,
                                          use_users_score=self.use_users_score)

    def parse_individual_page(self, response):
        pass


    def from_crawler(cls, crawler, *args, **kwargs):
        pass
