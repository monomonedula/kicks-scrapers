import scrapy


class RRSpider(scrapy.Spider):
    name = 'runrepeat'

    user_agent = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0'
    # user_agent = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'

    start_urls = [
        'https://runrepeat.com/ranking/rankings-of-running-shoes',
        # 'https://runrepeat.com/ranking/rankings-of-sneakers',
        # 'https://runrepeat.com/ranking/rankings-of-hiking-boots',
        # 'https://runrepeat.com/ranking/rankings-of-hiking-shoes',
        # 'https://runrepeat.com/ranking/rankings-of-hiking-sandals',
        # 'https://runrepeat.com/ranking/rankings-of-mountaineering-boots',
        # 'https://runrepeat.com/ranking/rankings-of-training-shoes',
        # 'https://runrepeat.com/best-basketball-shoes',
        # 'https://runrepeat.com/ranking/rankings-of-football-boots',
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        page = response.url
        filename = '%s.html' % page
        with open('rr.html', 'wb') as f:
            f.write(response.body)
        self.log('Saved file %s' % filename)
