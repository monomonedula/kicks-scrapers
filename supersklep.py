import logging
import re

from fluent import asynchandler, handler

import Parsing
from webutils.pageloader import SoupLoader
from itemgetter import ItemGetter
from basic_utils import (format_size_number, convert,
                         text_spaces_del, text_lower)
from dbhandling import parserdb

logger = logging.getLogger(__name__)


baselinks = [
    'https://supersklep.pl/buty-miejskie/meskie/no-{position}',
    'https://supersklep.pl/buty-miejskie/damskie/no-{position}',
]

scraper_name = 'supersklep'


def supersklep_parse(output=Parsing.database_writer):
    soup_loader = SoupLoader()
    ig = SupersklepIg(soup_loader)
    parser = Parsing.BaseParser(get_offers_list=get_offers_list,
                                get_item_dict=ig, soup_loader=soup_loader)
    link_gen = Parsing.links(baselinks=baselinks, maxpage=get_maxpage_func(soup_loader))
    output(parser(link_gen), scraper_name)


class SupersklepIg(ItemGetter):
    fields = [
        'get_link',
        'get_img_link',
        'get_colorway',
        'get_name',
        'get_sizes',
        'get_price',
        # 'get_id',
        'get_utc',
    ]

    @staticmethod
    def get_link(item, request):
        item['link'] = get_link(request['offer'])

    @staticmethod
    def get_img_link(item, request):
        item['img_link'] = get_img_link(request['offer'])

    @staticmethod
    def get_colorway(item, request):
        item['colorway'] = get_colorway(request['offer'])

    @staticmethod
    def get_sizes(item, request):
        item['sizes'] = get_sizes(request['offer'])

    @staticmethod
    def get_price(item, request):
        item['price'] = get_prices(request['offer'])

    @staticmethod
    def get_name(item, request):
        item['name'] = get_name(request['offer'])


def get_maxpage_func(soup_loader):
    def maxpage(link):
        bs_obj = soup_loader(link.format(position=1))
        div_tag = bs_obj.find("div", {"class": "pagination pull-right"})
        atags = div_tag.find_all("a", recursive=False)
        number = atags[-2]
        return int(number.text)
    return maxpage


def get_offers_list(soup):
    return soup.findAll("li", {"class": "pl--product"})


@text_spaces_del
@text_lower
def get_name(offer):
    a_tag = offer.find("a", {"class": "pl--image cvn-product"})
    return a_tag.attrs["data-name"]


@text_spaces_del
@text_lower
def get_brand(offer):
    return offer.find('a', {"class": "pl--image cvn-product"}).attrs['data-brand']


def get_link(offer):
    a_tag = offer.find("a", {"class": "pl--image cvn-product"})
    return a_tag.attrs["href"]


def get_img_link(offer):
    a_tag = offer.find("a", {"class": "pl--image cvn-product"})
    img = a_tag.find("img")
    return img.attrs["src"]


def get_prices(offer):
    div = offer.find("div", {"class": "pl--description"})
    price = div.find("span", {"class": "price"})
    new_price = price.find("span", class_="new")
    price = new_price if new_price else price
    num = re.sub('[^0-9]', '', price.text)
    num = float(num)
    if "PLN" in price.text:
        return convert("PLN", "USD", num)
    elif "€" in price.text:
        return convert("EUR", "USD", num)
    else:
        raise ValueError("No currency match")


def get_sizes(offer):
    span = offer.find("span", {"class": "variants"})
    trash, sizes = span.text.split(":", 1)
    sizes = sizes.split(";")
    db_sizes = []
    for s in sizes:
        try:
            db_sizes.append('eu' + format_size_number(s))
        except ValueError:
            continue
    return db_sizes


@text_spaces_del
@text_lower
def get_colorway(offer):
    a = offer.find("a", {"class": "pl--image cvn-product"})
    return a.attrs["data-dimension8"]


@text_lower
def get_id(offer, soup_loader):
    page = soup_loader(get_link(offer))
    li = page.find('li', text=re.compile('Kod producenta:'))
    if li:
        _, code = li.text.split(':', maxsplit=1)
        return code
    else:
        return ''


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

    if parserdb.is_finished(scraper_name):
        supersklep_parse()
    else:
        logger.error('Scraping job cannot be started because'
                     ' job with the same name %r is not finished. ' % scraper_name)
