import logging
from string import punctuation

from fluent import asynchandler, handler

import Parsing
from dbhandling import parserdb
from itemgetter import ItemGetter
from webutils.pageloader import SoupLoader
from basic_utils import (text_lower, text_spaces_del, convert,
                         format_size_number)


baselinks = [
    'https://chmielna20.pl/products/obuwie-mezczyzna-34eu/category,2/gender,M/size,{}/sizetype,EU/sort,1/page,{}',
    'https://chmielna20.pl/products/obuwie-kobieta-36eu/category,2/gender,W/size,{}/sizetype,EU/sort,1/page,{}',
]


logger = logging.getLogger(__name__)

punctuation_cleaner = str.maketrans(punctuation, ' ' * len(punctuation))

scraper_name = 'chmielna20'


def chmielna20_parse(output=Parsing.database_size_layer_writer):
    soup_loader = SoupLoader(bot=True)
    cg = ChmielnaIg(soup_loader)
    parser = Parsing.BaseParser(get_offers_list=get_offers_list,
                                get_item_dict=cg,
                                soup_loader=soup_loader)
    link_gen = links(baselinks, soup_loader=soup_loader)
    item_gen = parser(link_gen)
    return output(item_gen, scraper_name=scraper_name)


class ChmielnaIg(ItemGetter):
    fields = [
        'get_link',
        # 'get_colorway',
        # 'get_brand',
        'get_name',
        # 'get_model',
        'get_price',
        'get_sizes',
        'get_item_id',
        'get_img_link',
        'get_utc',
    ]

    @staticmethod
    def get_link(item, request):
        offer = request['offer']
        link = offer.find("a")
        item['link'] = link.attrs['href']

    @staticmethod
    def get_name(item, request):
        offer = request['offer']
        # item['name'] = get_name(offer) + ' ' + item['colorway']
        item['name'] = get_name(offer)

    @staticmethod
    def get_price(item, request):
        item['price'] = get_price(request['offer'])

    @staticmethod
    def get_sizes(item, request):
        item['sizes'] = get_sizes(request['size'])

    @staticmethod
    def get_item_id(item, request):
        item['item_id'] = get_item_id(request['offer'])

    @staticmethod
    def get_img_link(item, request):
        item['img_link'] = get_img_link(request['offer'])


def links(base_links, soup_loader):
    def get_sizes_list(link):
        soup = soup_loader(link.format(default_size, '1'))
        sizes_divs = soup.find_all('div', {'class': 'filter__size'})
        sizes_spans = [s.find('span') for s in sizes_divs]
        return [span['data-value'] for span in sizes_spans if span['data-type'] == 'EU']

    default_size = "34.5"
    mp = 100
    for baselink in base_links:
        sizes = get_sizes_list(baselink)
        logger.info('Sizes list for base link "{}" : {}'.format(baselink, sizes))
        for size in sizes:
            yield {'link': baselink.format(size, mp), 'size': size.replace('|', '/')}


def get_offers_list(soup):
    return soup.find_all("div", class_="col-sm-4 col-md-3 col-xs-6 products__item")


def get_sizes(size):
    sizes = ['eu' + format_size_number(size)]
    return sizes


@text_lower
@text_spaces_del
def get_name(offer):
    p = offer.find('p', class_='products__item-name')
    name = str(p.text)
    if not name:
        raise ValueError('"alt" attribute in "a" tag is empty!')
    name = name.replace("buty", "")
    return name


@text_lower
@text_spaces_del
def get_item_id(offer):
    name = get_name(offer)
    try:
        if '(' in name:
            _, item_id = name.split('(')
            item_id, _ = item_id.split(')')
            return item_id
    except ValueError:
        pass

    logger.warning("Unable to find item id in name '{}'".format(name))
    return ''


def get_img_link(offer):
    img = offer.find("img")
    return img.attrs['src']


def get_price(offer):
    prices = offer.find('p', class_="products__item-price")
    spans = prices.find_all("span")
    if len(spans) == 1:
        price = spans[0]
    else:
        price = spans[1]

    price = price.text.replace("PLN", "")
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
    if parserdb.is_finished(scraper_name):
        chmielna20_parse()
    else:
        logger.error('Scraping job cannot be started because'
                     ' job with the same name %r is not finished. ' % scraper_name)
