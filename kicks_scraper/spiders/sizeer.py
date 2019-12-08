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
            yield scrapy.Request(
                url=url.format(page=1),
            )

    def parse(self, response):
        for item in SizeerPage(response).items():
            yield item.as_scraper_item()
        yield scrapy.Request(
            url=SizeerPage(response).next_page_url(),
        )


class SizeerPage:
    def __init__(self, response):
        self._response = response

    def items(self) -> Iterable["SizeerItem"]:
        # TODO: implement items method
        pass

    def next_page_url(self) -> str:
        pass


class SizeerItem:
    def __init__(self, page):
        self._page = page

    def as_scraper_item(self) -> KicksScraperItem:
        # TODO: implement as_scraper_item method
        pass
