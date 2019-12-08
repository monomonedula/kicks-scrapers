import scrapy
from typing import Iterable

from scrapy import Selector

from basic_utils import format_size_number, convert
from kicks_scraper.items import KicksScraperItem


class SizeerSpider(scrapy.Spider):
    name = "sizeer"

    user_agent = (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"
    )

    def start_requests(self):
        for url in [
            "https://sklep.sizeer.com/meskie/buty?limit=120&page={page}",
            "https://sklep.sizeer.com/damskie/buty?limit=120&page={page}",
        ]:
            yield scrapy.Request(url=url.format(page=1),)

    def parse(self, response):
        for item in SizeerPage(response).items():
            yield item.as_scraper_item()
        if SizeerPage(response).next_page_url():
            yield scrapy.Request(url=SizeerPage(response).next_page_url())


class SizeerPage:
    def __init__(self, response):
        self._response = response

    def items(self) -> Iterable["SizeerItem"]:
        for tag in self._response.xpath('//div[@id="js-offerList"]/div').getall():
            yield SizeerItem(Selector(text=tag, type="xml"))

    def next_page_url(self) -> str:
        url = self._response.xpath(
            "/html/body/section[1]/main/div/div/div[2]/form/div/div[3]/nav/a[2]/@href"
        ).get()
        if url:
            return "http://sklep.sizeer.com" + url


class SizeerItem:
    def __init__(self, selector):
        self._selector = selector

    def as_scraper_item(self) -> KicksScraperItem:
        url = "http://sklep.sizeer.com" + self._selector.xpath("//a/@href").get()
        return KicksScraperItem(
            id=url,
            url=url,
            item_id=self._selector.xpath("/div/@data-ga-id").get(),
            name=self._selector.xpath("/div/@data-ga-name").get().lower(),
            price=self._selector.xpath("/div/@data-price").get(),
            img_url=self._selector.xpath("//a/img/@data-src").get(),
            sizes=SizeerItemSizes(self._selector).as_list(),
        )


class SizeerItemSizes:
    def __init__(self, selector):
        self._selector = selector

    def as_list(self):
        sizes = []
        for val in self._selector.xpath(
            '//div[@class="b-itemList_sizes js-variant_size is-active"]/div/span/text()'
        ).getall():
            sizes.append("eu" + format_size_number(val.strip()))
        return sizes


class SizeerItemPrice:
    def __init__(self, selector):
        self._selector = selector

    def as_int(self):
        return convert(
            "PLN", "USD", float(self._selector.xpath("/div/@data-price").get())
        )
