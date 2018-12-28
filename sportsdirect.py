import logging
import re
from time import sleep

from fluent import asynchandler, handler

from dbhandling import parserdb
import Parsing
from webutils.pageloader import SoupLoader
from basic_utils import (format_size_number, convert, text_spaces_del, text_lower)
from itemgetter import ItemGetter


logger = logging.getLogger(__name__)


baselinks = [
    'https://pl.sportsdirect.com/mens/mens-trainers#dcp={position}&dppp=100&OrderBy=rank',
    'https://pl.sportsdirect.com/mens/mens-hi-tops#dcp={position}&dppp=100&OrderBy=rank&Filter=none',
    'https://pl.sportsdirect.com/mens/mens-basketball-shoes#dcp={position}&dppp=100&OrderBy=rank&Filter=none',
    'https://pl.sportsdirect.com/mens/mens-canvas-shoes#dcp={position}&dppp=100&OrderBy=rank',
    'https://pl.sportsdirect.com/mens/mens-skate-shoes#dcp={position}&dppp=100&OrderBy=rank',
    'https://pl.sportsdirect.com/mens/mens-court-and-indoor-trainers#dcp={position}&dppp=100&OrderBy=rank',
    'https://pl.sportsdirect.com/ladies/ladies-canvas-shoes#dcp={position}&dppp=100&OrderBy=rank',
    'https://pl.sportsdirect.com/ladies/ladies-trainers#dcp={position}&dppp=100&OrderBy=rank',
    'https://pl.sportsdirect.com/ladies/ladies-indoor-and-court-trainers#dcp={position}&dppp=100&OrderBy=rank',
]

scraper_name = 'sportsdirect'


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
        sportsdirect_parse()
    else:
        logger.error('Scraping job cannot be started because'
                     ' job with the same name %r is not finished. ' % scraper_name)


def sportsdirect_parse(output=Parsing.database_writer):
    soup_loader = SoupLoader(bot=True)
    ig = SportsDirectIg(soup_loader)
    parser = Parsing.BaseParser(get_offers_list=get_offers_list,
                                get_item_dict=ig,
                                soup_loader=soup_loader)
    link_generator = Parsing.links(baselinks, get_maxpage_func(soup_loader))
    item_generator = parser(link_generator)
    return output(item_generator, scraper_name)


class SportsDirectIg(ItemGetter):
    fields = [
        'get_link',
        'get_brand',
        'get_sizes',
        'get_colorway',
        'get_name',
        'get_model',
        'get_price',
        'get_img_link',
        'get_utc',
    ]

    @staticmethod
    def get_link(item, request):
        item['link'] = get_link(request['offer'])

    @staticmethod
    def get_brand(item, request):
        item['brand'] = get_brand(request['offer'])

    def get_sizes(self, item, request):
        page = self._get_page(item['link'])
        item['sizes'] = get_sizes(page, item['brand'])

    @staticmethod
    def get_name(item, request):
        item['name'] = get_name(request['offer'])

    def get_colorway(self, item, request):
        page = self._get_page(item['link'])
        item['colorway'] = get_colorway(page)

    @staticmethod
    def get_model(item, request):
        item['model'] = get_model(request['offer'])

    @staticmethod
    def get_price(item, request):
        item['price'] = get_price(request['offer'])

    @staticmethod
    def get_img_link(item, request):
        item['img_link'] = get_img_link(request['offer'])

    def _load_page(self, link):
        sleep(0.4)
        self._page_cache = (self.soup_loader(link.replace('pl.', 'www.')), link)


def get_maxpage_func(soup_loader):
    def maxpage(link):
        link = link.format(position=1)
        soup = soup_loader(link)
        page_tags = soup.find_all("a", {"class": "swipeNumberClick"})
        if not page_tags:
            return 1
        nums = []
        for a in page_tags:
            number = a.get("data-dcp")
            number = int(number)
            nums.append(number)
        return max(nums)
    return maxpage


def get_name(offer):
    return get_brand(offer) + ' ' + get_model(offer)


def get_model(offer):
    model = offer.find("span", {"class": "productdescriptionname"})
    return model.text


def get_brand(offer):
    brand = offer.find("span", {"class": "productdescriptionbrand"})
    return brand.text


def get_img_link(offer):
    tag = offer.find("img", {"class": "rtimg MainImage img-responsive"})
    if not tag:
        tag = offer.find("img", {"class": "rtimg MainImage img-hide img-responsive"})
        return tag.attrs['data-original']
    return tag.attrs["src"]


def get_link(offer):
    tag = offer.find("a", {"class": "s-product-sache"})
    link = tag.attrs["href"]
    if 'sportsdirect.com' not in link:
        return 'https://pl.sportsdirect.com' + link
    return link


def get_price(offer):
    span = offer.find("span", attrs={"class": re.compile("CurrencySizeMedium curprice")})
    price = span.text.replace(",", ".")
    price = float(re.sub('[^\d.]', '', price))
    return convert("PLN", "USD", price)


def get_sizes(page, brand):
    lis = page.find_all('li', class_=re.compile('tooltip sizeButtonli ?$'))
    db_sizes = []
    for li in lis:
        s = li.a.text
        from_parentheses = s[s.find("(")+1:s.find(")")]
        db_sizes.append('eu' + format_size_number(from_parentheses))
    return db_sizes


@text_spaces_del
@text_lower
def get_colorway(page):
    return page.find('span', {'id': re.compile('dnn_ctr\d+_ViewTemplate_ctl00_ctl10_colourName')}).text


def get_offers_list(soup):
    return soup.find_all("div", {"class": "s-productthumbbox"})
