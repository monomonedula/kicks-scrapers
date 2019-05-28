import logging
import re
from time import sleep

from fluent import asynchandler, handler

import Scraping
from dbhandling.indexing import SessionedWriter
from webutils.pageloader import SoupLoader
from basic_utils import (convert, text_spaces_del, text_lower, format_size_number)
from itemgetter import LinkIdentifiedItemGetter as ItemGetter

baselinks = [
    'https://worldbox.pl/products/mezczyzna-obuwie/category,2/gender,M/item,72/page,{position}',
    'https://worldbox.pl/products/kobieta-obuwie/category,2/gender,W/item,72/page,{position}',
]

logger = logging.getLogger(__name__)

scraper_name = 'worldbox'


def worldbox_scrape():
    soup_loader = SoupLoader()
    wb_ig = WorldboxIg(soup_loader)
    scraper = Scraping.BaseScraper(get_offers_list=get_offers_list, get_item_dict=wb_ig,
                                   soup_loader=soup_loader)
    link_gen = Scraping.links(baselinks, get_maxpage_func(soup_loader))
    return scraper(links=link_gen)


class WorldboxIg(ItemGetter):
    fields = [
        'get_url',
        'get_name',
        # 'get_colorway',
        'get_price',
        'get_sizes',
        'get_img_url',
    ]

    @staticmethod
    def get_url(item, request):
        item['url'] = get_link(request['offer'])

    @staticmethod
    def get_name(item, request):
        item['name'] = get_name(request['offer'])

    def get_colorway(self, item, request):
        item['colorway'] = get_colorway(request['offer'], self.soup_loader)

    @staticmethod
    def get_price(item, request):
        item['price'] = get_price(request['offer'])

    @staticmethod
    def get_sizes(item, request):
        item['sizes'] = get_sizes(request['offer'])

    @staticmethod
    def get_img_url(item, request):
        item['img_url'] = get_img_link(request['offer'])


def get_maxpage_func(soup_loader):
    def maxpage(link):
        bs_obj = soup_loader(link.format(position=1))
        ul = bs_obj.find("ul", {"class": "pagination"})
        lis = ul.findAll("li")
        mxpg = lis[-2].text
        mxpg = re.sub(r'\D', '', mxpg)
        return int(mxpg)

    return maxpage


@text_lower
@text_spaces_del
def get_name(offer):
    name = offer.a.attrs["title"].lower()
    return name.replace("buty", "")


@text_lower
@text_spaces_del
def get_item_id(offer):
    code = offer.find("p", {"class": "__code"})
    code = code.text
    return code.split(": ", 1)[1].lower()


def get_img_link(offer):
    return offer.img.attrs['data-echo']


def get_link(offer):
    a = offer.find("a", {"class": None})
    return a.attrs["href"]


def get_price(offer):
    price_tag = offer.find("span", {"class": "price-tag"})
    pln = price_tag.find("span", {"data-currency_key": "PLN"}).text
    pln = re.sub("[^0-9]", "", pln)
    pln = float(pln)
    return convert("PLN", "USD", pln)


def get_sizes(offer):
    div = offer.find("div", {"class": "more"})
    li = div.findAll("li")
    sizes = [list_item.attrs["data-sizeeu"] for list_item in li]
    db_sizes = []
    for s in sizes:
        db_sizes.append('eu' + format_size_number(s))
    return db_sizes


def get_offers_list(soup):
    container = soup.find("", {"class": "row product__container"})
    return container.findAll("div", recursive=False)


@text_lower
@text_spaces_del
def get_colorway(offer, soup_loader):
    sleep(0.3)
    link = get_link(offer)
    soup = soup_loader(link)
    descr = soup.find("div", class_="description__main")
    if descr:
        c = re.compile("Kolor")
        color = descr.find(text=c)
        if color:
            strings = list(color.parent.strings)
            for s, i in enumerate(strings):
                if s == color:
                    return str(strings[i + 1])
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
    items = worldbox_scrape()
    writer = SessionedWriter(scraper_name, items)
    writer.write_items()
