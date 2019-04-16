import logging
import json
import re

from fluent import asynchandler, handler

import Scraping
from dbhandling.indexing import SessionedWriter
from webutils.pageloader import LxmlSoupLoader
from basic_utils import (convert,
                         text_lower, format_size_number)
from itemgetter import LinkIdentifiedItemGetter as ItemGetter

logger = logging.getLogger(__name__)

baselinks = [
    'https://www.zalando.pl/obuwie-meskie-tenisowki-trampki/?p={position}',
    'https://www.zalando.pl/obuwie-sportowe-mezczyzni/?p={position}',
    'https://www.zalando.pl/obuwie-meskie-polbuty/?p={position}',
    'https://www.zalando.pl/obuwie-damskie-tenisowki-trampki/?p={position}',
    'https://www.zalando.pl/polbuty/?p={position}',
    'https://www.zalando.pl/obuwie-sportowe-kobiety/?p={position}',
    'https://www.zalando.pl/obuwie-sportowe-dzieci/?p={position}',
    'https://www.zalando.pl/obuwie-dzieciece-tenisowki-trampki/?p={position}',
    'https://www.zalando.pl/obuwie-dzieciece-polbuty/?p={position}',
]

scraper_name = 'zalando'


def zalando_scrape():
    soup_loader = LxmlSoupLoader(use_proxies=False)
    ig = ZalandoIg(soup_loader)
    scraper = Scraping.BaseScraper(get_offers_list=get_offers_list, get_item_dict=ig,
                                   soup_loader=soup_loader)

    link_generator = Scraping.links(baselinks, maxpage=get_maxpage(soup_loader))
    return scraper(link_generator)


class ZalandoIg(ItemGetter):
    fields = [
        'get_url',
        'get_name',
        'get_price',
        'get_sizes',
        'get_img_url',
    ]

    @staticmethod
    def get_url(item, request):
        item['url'] = get_link(request['offer'])

    @staticmethod
    def get_name(item, request):
        item['name'] = get_brand(request['offer']) + ' ' + get_name(request['offer'])

    @staticmethod
    def get_price(item, request):
        item['price'] = get_price(request['offer'])

    @staticmethod
    def get_sizes(item, request):
        item['sizes'] = get_sizes(request['offer'])

    @staticmethod
    def get_img_url(item, request):
        item['img_url'] = get_img_link(request['offer'])


def get_offers_list(page):
    script_tag = page.cssselect('#z-nvg-cognac-props')
    json_text = script_tag[0].text
    json_text = json_text.split('[', maxsplit=2)[2]
    json_text = json_text.rsplit(']', maxsplit=2)[0]
    return json.loads(json_text)['articles']


@text_lower
def get_name(offer):
    return offer['name']


@text_lower
def get_brand(offer):
    return offer['brand_name']


def get_price(offer):
    price = offer['price']['promotional']
    price = price.replace(',', '.')
    price = re.sub(r'[^\d.]', '', price)
    price = float(price)
    return convert(frm='PLN', to='USD', amount=price)


def get_sizes(offer):
    sizes = offer['sizes']
    return ['eu' + format_size_number(size) for size in sizes]


def get_link(offer):
    return 'https://www.zalando.pl/' + offer['url_key'] + '.html'


def get_img_link(offer):
    try:
        return 'https://mosaic04.ztat.net/vgs/media/catalog-lg/' + offer['media'][0]['path']
    except (KeyError, IndexError):
        return None


def get_maxpage(soup_loader):
    def maxpage(link):
        page = soup_loader(link.format(position=1))
        script_tag = page.cssselect('#z-nvg-cognac-props')
        json_text = script_tag[0].text
        json_text = json_text.split('[', maxsplit=2)[2]
        json_text = json_text.rsplit(']', maxsplit=2)[0]
        data = json.loads(json_text)
        return data['pagination']['page_count']

    return maxpage


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
    items = zalando_scrape()
    writer = SessionedWriter(scraper_name, items)
    writer.write_items()
