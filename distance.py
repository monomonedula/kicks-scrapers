import logging
import re

from fluent import asynchandler, handler

import Parsing
from webutils.pageloader import LxmlSoupLoader
from basic_utils import (convert,
                         text_spaces_del, text_lower,
                         format_size_number)
from itemgetter import ItemGetter
from dbhandling import parserdb


logger = logging.getLogger(__name__)

baselinks = [
    'https://distance.pl/plec/mezczyzna.html?page={position}',
    'https://distance.pl/plec/kobieta.html?page={position}',
    'https://distance.pl/plec/junior.html?page={position}',
]

scraper_name = 'distance'


def main():
    log_format = {
        'where': '%(module)s.%(funcName)s',
        'type': '%(levelname)s',
        'stack_trace': '%(exc_text)s',
    }

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('')
    logger.setLevel(level=logging.INFO)
    h = asynchandler.FluentHandler('kicks.scraper', host='localhost', port=24224)
    h.setLevel(level=logging.INFO)
    formatter = handler.FluentRecordFormatter(log_format)
    h.setFormatter(formatter)
    logging.getLogger('').addHandler(h)

    if parserdb.is_finished(scraper_name):
        distance_scrape()
    else:
        logger.error('Scraping job cannot be started because'
                     ' job with the same name %r is not finished. ' % scraper_name)


def distance_scrape(output=Parsing.database_writer):
    soup_loader = LxmlSoupLoader()
    ig = DistanceIg(soup_loader)
    parser = Parsing.BaseParser(get_offers_list=get_offers_list, get_item_dict=ig,
                                soup_loader=soup_loader)

    link_generator = Parsing.links(baselinks, maxpage=get_maxpage(soup_loader))
    item_generator = parser(link_generator)
    return output(item_generator, scraper_name)


class DistanceIg(ItemGetter):
    fields = [
        'get_link',
        'get_name',
        'get_img_link',
        'get_price',
        'get_sizes',
        'get_utc',
    ]

    @staticmethod
    def get_link(item, request):
        item['link'] = get_link(request['offer'])

    @staticmethod
    def get_name(item, request):
        item['name'] = get_name(request['offer'])

    @staticmethod
    def get_img_link(item, request):
        item['img_link'] = get_img_link(request['offer'])

    @staticmethod
    def get_price(item, request):
        item['price'] = get_price(request['offer'])

    @staticmethod
    def get_sizes(item, request):
        item['sizes'] = get_sizes(request['offer'])


def get_link(offer):
    return offer.cssselect('a:nth-child(1)')[0].attrib['href']


@text_lower
@text_spaces_del
def get_name(offer):
    return offer.cssselect('a:nth-child(1) > h4:nth-child(2)')[0].text


def get_img_link(offer):
    return offer.cssselect('a:nth-child(1) >'
                           ' div:nth-child(1) >'
                           ' img:nth-child(1)')[0].attrib['src'].strip('//')


def get_price(offer):
    price = offer.cssselect('a > p > em')[0].text
    price = re.sub('[^\d,]', '', price)
    price = price.replace(',', '.', 1)
    return convert(frm='PLN', to='USD', amount=float(price))


def get_sizes(offer, brand=None):
    sizes = offer.find_class('pList__item__sizes')[0].getchildren()
    sizes = (s.text for s in sizes)
    # formated_sizes = []
    # for size in sizes:
    #     for sz in size_to_db_format('eu', size, brand) or ['eu' + format_size_number(size)]:
    #         formated_sizes.append(sz)
    # return formated_sizes
    return ['eu' + format_size_number(size) for size in sizes]


def get_offers_list(page):
    return page.cssselect('html body div.main_wrapper.js--sidecart--main_wrapper'
                          ' div#wrapper.wrapper div.container'
                          ' div.productsWrapper ul#ga-products.pList')[0].getchildren()


def get_maxpage(soup_loader):
    def maxpage(link):
        link = link.format(position=1)
        pg = soup_loader(link)
        return int(pg.cssselect('#wrapper > div.container >'
                                ' div.productsWrapper > div.pagination >'
                                ' div > a.last')[0].text)
    return maxpage
