import logging
import re
from time import sleep

from fluent import asynchandler, handler

import Scraping
from dbhandling.indexing import SessionedWriter
from webutils.pageloader import SoupLoader
from basic_utils import (format_size_number,
                         convert, text_spaces_del, text_lower)
from itemgetter import ItemGetter

logger = logging.getLogger(__name__)

baselinks = [
    "https://www.mandmdirect.pl/01/m%C4%99skie/obuwie/{position}",
    "https://www.mandmdirect.pl/01/damskie/obuwie/{position}",
]

scraper_name = 'mandmdirect'


def mandmdirect_parse():
    soup_loader = SoupLoader(bot=False, use_proxies=True)
    ig = MandmdirectIg(soup_loader)
    links = Scraping.links(baselinks, get_maxpage_func(soup_loader))
    scraper = Scraping.BaseScraper(get_offers_list=get_offers_list, get_item_dict=ig,
                                   soup_loader=soup_loader)
    return scraper(links)


class MandmdirectIg(ItemGetter):
    fields = [
        'get_link',
        'get_name',
        'get_price',
        'get_sizes',
        'get_img_link',
        'get_utc',
    ]

    def _load_page(self, link):
        sleep(0.4)
        self._page_cache = (self.soup_loader(link.replace('.pl', '.com')), link)

    @staticmethod
    def get_link(item, request):
        item['link'] = get_link(request['offer'])

    def get_name(self, item, request):
        page = self._get_page(item['link'])
        item['name'] = get_name(page)

    def get_sizes(self, item, request):
        item['sizes'] = get_sizes(request['offer'])

    @staticmethod
    def get_price(item, request):
        item['price'] = get_prices(request['offer'])

    @staticmethod
    def get_img_link(item, request):
        item['img_link'] = get_img_link(request['offer'])


def get_maxpage_func(soup_loader):
    def maxpage(link):
        default_link = link.format(position=1)
        bsobj = soup_loader(default_link)
        pgnums = bsobj.find("span", {"class": "pageNumbers"})
        pgnums = pgnums.text.split("z")[1]
        return int(pgnums)

    return maxpage


def get_offers_list(soup):
    classes = re.compile("span3 item plitem")
    return soup.find_all("div", {"class": classes})


@text_lower
@text_spaces_del
def get_name(item_page):
    return item_page.find('title').text.replace('Buy', '')


def get_link(offer):
    a = offer.find("a", {"id": False})
    return "https://www.mandmdirect.com" + a.attrs["href"]


def get_img_link(offer):
    div = offer.find("div", {"class": "itemimage"})
    img = div.find("img")
    return img.attrs["src"]


def get_sizes(offer):
    ul = offer.find("ul", {"class": "sizeSelect dropdown-menu"})
    available = ul.findAll("a")
    sizes = []
    for a in available:
        try:
            size = re.findall(r'\[?Euro\]? (\d\d\.?\d?)', a.text)[0]
        except IndexError:
            raise ValueError('Cannot extract euro size from string "{}"'.format(a.text))
        sizes.append('eu' + format_size_number(size))
    return sizes


def get_prices(offer):
    price_tag = offer.find("span", {"class": "price"})
    price = price_tag.text.replace(',', '.')
    price = price.replace('zł', '')
    price = float(price)
    return convert("PLN", "USD", price)


if __name__ == '__main__':
    log_format = {
        'where': '%(module)s.%(funcName)s',
        'type': '%(levelname)s',
        'stack_trace': '%(exc_text)s',
    }

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('')
    logger.setLevel(level=logging.INFO)
    h = asynchandler.FluentHandler('kicks.scraper.%s' % scraper_name, host='localhost', port=24224)
    h.setLevel(level=logging.INFO)
    formatter = handler.FluentRecordFormatter(log_format)
    h.setFormatter(formatter)
    logging.getLogger('').addHandler(h)
    items = mandmdirect_parse()
    writer = SessionedWriter(scraper_name, items)
    writer.write_items()
