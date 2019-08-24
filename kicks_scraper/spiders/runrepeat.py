import json
from typing import Iterable, Callable, Union

import scrapy

from ..items import RunRepeatItem


def total_items_num(response):
    data = json.loads(response.text)
    return data['aggregations']['stats']['total_count_any_size']


def rr_requests(urls: Iterable['PaginatingJsonURL'], callback: Union[None, Callable]):
    for p_url in urls:
        yield scrapy.Request(url=p_url.url(),
                             callback=callback)


def limited_urls(initial_url: 'PaginatingJsonURL', limit: int):
    p_url = initial_url
    while p_url.start < limit:
        yield p_url
        p_url = p_url.next()


class PaginatingJsonURL:
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

    category_url_packages = [
        # sneakers
        (
            'https://runrepeat.com/get-stats?from=0&size=30&orderBy'
            '=score&order=desc&r=1564742822404&filter%5B%5D=410&filte'
            'r%5B%5D=6254&filter%5B%5D=3591&c_id=3&f_id=4',


            'https://runrepeat.com/get-documents?'
            'from={from_item}&size={size}&orderBy=score&order=desc&r=1564648578712&filter'
            '%5B%5D=410&filter%5B%5D=6254&filter%5B%5D=3591&c_id=3&f_id=4'
        ),

        # running shoes
        (
            'https://runrepeat.com/get-stats?from=0&size=30&orderBy=score&order='
            'desc&r=1564742189280&filter%5B%5D=1&filter%5B%5D=6214&c_id=2&f_id=2',

            'https://runrepeat.com/get-documents?from={from_item}&size={size}&orderBy=score'
            '&order=desc&r=1564742189274&filter%5B%5D=1&filter%5B%5D=6214&c_id=2&f_id=2'),

        # hiking boots
        (
            'https://runrepeat.com/get-stats?from=0&size=30&orderBy=score&order=desc&'
            'r=1564742960269&filter%5B%5D=4493&filter%5B%5D=6274&filter%5B%5D=4710&c_id=9&f_id=15',

            'https://runrepeat.com/get-documents?from={from_item}&size={size}&orderBy='
            'score&order=desc&r=1564742959922&filter%5B%5D=4493&filter%5B%5D=6274&filter%5B%5D=4710&c_id=9&f_id=15'
        ),
        # hiking shoes
        (
            'https://runrepeat.com/get-stats?from=0&size=30&orderBy=score&order=desc&r=1564743143007&filter%5B%5D'
            '=4843&filter%5B%5D=6278&filter%5B%5D=5060&c_id=10&f_id=17',

            'https://runrepeat.com/get-documents?from={from_item}&size={size}&'
            'orderBy=score&order=desc&r=1564743142391&filter%5B%5D=4843&filter%5B%5D'
            '=6278&filter%5B%5D=5060&c_id=10&f_id=17'
        ),

        # hiking sandals
        (
            'https://runrepeat.com/get-stats?from=0&size=30&orderBy=score&order=desc&'
            'r=1564743310025&filter%5B%5D=5193&filter%5B%5D=6282&filter%5B%5D=5410&c_id=11&f_id=19',

            'https://runrepeat.com/get-documents?from={from_item}&size={size}&orderBy=score&order=desc&'
            'r=1564743310020&filter%5B%5D=5193&filter%5B%5D=6282&filter%5B%5D=5410&c_id=11&f_id=19'
        ),

        # to be continued
    ]

    templates = {
        'sneakers': 'https://runrepeat.com/get-documents?'
                    'from={from_item}&size={size}&orderBy=score&order=desc&r=1564648578712&filter'
                    '%5B%5D=410&filter%5B%5D=6254&filter%5B%5D=3591&c_id=3&f_id=4',
    }

    def start_requests(self):
        for stats_json_url, url_template in self.category_url_packages:
            meta = {'template': url_template}
            yield scrapy.Request(url=stats_json_url,
                                 callback=self.parse,
                                 meta=meta)

    def parse(self, response):
        total_items = total_items_num(response)
        template = response.meta['template']

        yield from rr_requests(
            urls=limited_urls(
                initial_url=PaginatingJsonURL(0, 30, template),
                limit=total_items
            ),
            callback=self.parse_json,
        )

    @staticmethod
    def parse_json(response):
        data = json.loads(response.text)
        for item in data:
            yield RunRepeatItem.from_runrepeat_json_dict(item,
                                                         use_users_score=False)
