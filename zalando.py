import logging
import json
import re

from fluent import asynchandler, handler

from dbhandling import parserdb
import Parsing
from webutils.pageloader import LxmlSoupLoader
from basic_utils import (convert,
                         text_lower, format_size_number)
from itemgetter import ItemGetter


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
        zalando_scrape()
    else:
        logger.error('Scraping job cannot be started because'
                     ' job with the same name %r is not finished. ' % scraper_name)


def zalando_scrape(output=Parsing.database_writer):
    soup_loader = LxmlSoupLoader(use_proxies=False)
    ig = ZalandoIg(soup_loader)
    parser = Parsing.BaseParser(get_offers_list=get_offers_list, get_item_dict=ig,
                                soup_loader=soup_loader)

    link_generator = Parsing.links(baselinks, maxpage=get_maxpage(soup_loader))
    item_generator = parser(link_generator)
    return output(item_generator, "zalando")


class ZalandoIg(ItemGetter):
    fields = [
        'get_link',
        'get_name',
        'get_price',
        'get_sizes',
        'get_img_link',
        'get_utc',
    ]

    @staticmethod
    def get_link(item, request):
        item['link'] = get_link(request['offer'])

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
    def get_img_link(item, request):
        item['img_link'] = get_img_link(request['offer'])


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
    price = re.sub('[^\d.]', '', price)
    price = float(price)
    # flags = offer.get('flags', [])
    # for f in flags:
    #     if 'discountRate' in f.values() and '%' in f.get('value', ''):
    #         discount = re.sub('\D', '', f['value'])
    #         discount = float(discount)
    #         price *= 1 - (discount / 100)
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
