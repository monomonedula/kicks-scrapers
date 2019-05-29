import logging

from fluent import asynchandler, handler

import Scraping
from dbhandling.indexing import SessionedWriter
from webutils.pageloader import SoupLoader
from basic_utils import (only_digits, format_size_number, convert,
                         text_spaces_del, text_lower)
from itemgetter import LinkIdentifiedItemGetter as ItemGetter


logger = logging.getLogger(__name__)

baselinks = [
    'https://sklep.sizeer.com/meskie/buty?limit=120&page={position}',
    'https://sklep.sizeer.com/damskie/buty?limit=120&page={position}',
]

scraper_name = 'sizeer'


def sizeer_parse():
    soup_loader = SoupLoader(use_proxies=True)
    ig = SizeerIg(soup_loader)
    parser = Scraping.BaseScraper(get_offers_list=get_offers_list, get_item_dict=ig,
                                  soup_loader=soup_loader)

    link_generator = Scraping.links(baselinks, maxpage=get_maxpage(soup_loader))
    item_generator = parser(link_generator)
    return item_generator


class SizeerIg(ItemGetter):
    fields = [
        'get_url',
        'get_brand',
        'get_img_url',
        'get_name',
        'get_id',
        'get_price',
        'get_sizes',
    ]

    @staticmethod
    def get_url(item, request):
        item.url = get_link(request['offer'])

    @staticmethod
    def get_brand(item, request):
        item.brand = get_brand(request['offer'])

    @staticmethod
    def get_img_url(item, request):
        item.img_url = get_img_link(request['offer'])

    @staticmethod
    def get_name(item, request):
        item.name = get_name(request['offer'])

    @staticmethod
    def get_id(item, request):
        item.item_id = get_id(request['offer'])

    @staticmethod
    def get_price(item, request):
        item.price = get_prices(request['offer'])

    @staticmethod
    def get_sizes(item, request):
        item.sizes = get_sizes(request['offer'])


def get_offers_list(soup):
    container = soup.find("", {"id": "js-offerList"})
    return container.findAll("div", recursive=False)


def get_maxpage(soup_loader):
    def maxpage(link):
        bs_obj = soup_loader(link.format(position="1"))
        nav = bs_obj.find("nav", {"class": "m-pagination"})
        num_string = nav.find("span", class_=None).text
        return int(only_digits(num_string))
    return maxpage


@text_lower
@text_spaces_del
def get_name(offer):
    return offer.attrs["data-ga-name"]


@text_lower
@text_spaces_del
def get_brand(offer):
    brand_raw = offer.attrs["data-brand"]
    return brand_raw


@text_lower
@text_spaces_del
def get_id(offer):
    return offer.attrs["data-ga-id"]


def get_img_link(offer):
    return "https://sklep.sizeer.com" + offer.a.img.attrs["data-src"]


def get_link(offer):
    return "http://sklep.sizeer.com" + offer.a.attrs["href"]


def get_prices(offer):
    price = offer.attrs["data-price"]
    price = float(price)
    return convert("PLN", "USD", price)


def get_sizes(offer):
    div = offer.find(attrs={"class": "m-productsBox_variantSizes js-variant_size is-active"})
    try:
        spans = div.findAll("span")
    except AttributeError:
        return []

    sizes = []
    for val in (span.text for span in spans):
        sizes.append('eu' + format_size_number(val))
    return sizes


if __name__ == '__main__':
    log_format = {
        'where': '%(module)s.%(funcName)s',
        'type': '%(levelname)s',
        'stack_trace': '%(exc_text)s',
    }

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger('')
    logger.setLevel(level=logging.DEBUG)
    h = asynchandler.FluentHandler('kicks.scraper.%s' % scraper_name, host='localhost', port=24224)
    h.setLevel(level=logging.DEBUG)
    formatter = handler.FluentRecordFormatter(log_format)
    h.setFormatter(formatter)
    logging.getLogger('').addHandler(h)
    items = sizeer_parse()
    writer = SessionedWriter(scraper_name, items)
    writer.write_items()
