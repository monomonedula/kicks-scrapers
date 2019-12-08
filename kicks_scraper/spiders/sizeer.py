import scrapy


class SizeerSpider(scrapy.Spider):
    name = "sizeer"

    user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0'

    def start_requests(self):
        for url in [
            'https://sklep.sizeer.com/meskie/buty?limit=120&page={page}',
            'https://sklep.sizeer.com/damskie/buty?limit=120&page={page}',
        ]:
            meta = {"template": url}
            yield scrapy.Request(
                url=url.format(page=1),
                meta=meta
            )

    def parse(self, response):
        # TODO: implement parse
        pass
