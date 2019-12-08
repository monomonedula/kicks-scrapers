import scrapy
from typing import Iterable

from kicks_scraper.items import KicksScraperItem


class SizeerSpider(scrapy.Spider):
    name = "sizeer"

    user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0'

    def start_requests(self):
        for url in [
            'https://sklep.sizeer.com/meskie/buty?limit=120&page={page}',
            'https://sklep.sizeer.com/damskie/buty?limit=120&page={page}',
        ]:
            meta = {"template": url, "page": 1}
            yield scrapy.Request(
                url=url.format(page=1),
                meta=meta
            )

    def parse(self, response):
        # TODO: finish parse method
        template = response.meta['template']
        page = response.meta['page']
        

class SizeerPage:
    def __init__(self):
        pass

    def items(self) -> Iterable["SizeerItem"]:
        # TODO: implement items method
        pass


class SizeerItem:
    def __init__(self, page):
        self._page = page

    def as_scraper_item(self) -> KicksScraperItem:
        # TODO: implement as_scraper_item method
        pass
