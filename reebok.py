import re
import logging

from fluent import asynchandler, handler

import Parsing
from dbhandling import parserdb
from itemgetter import ItemGetter
from webutils.pageloader import SoupLoader
from basic_utils import (text_spaces_del, text_lower,
                         convert, format_size_number)

logger = logging.getLogger(__name__)


reebok_baselinks = [
    'https://www.reebok.pl/kobiety-buty?sz={ipp}&prefn1=sizeSearchValue&prefv1={size}&start={position}',
    'https://www.reebok.pl/mezczyzni-buty?sz={ipp}&prefn1=sizeSearchValue&prefv1={size}&start={position}',
]

scraper_name = 'reebok'


def reebok_parse(*, output=Parsing.database_size_layer_writer, ipp=120):
    if ipp not in (120, 24):
        raise ValueError('Unknown items per page value: {}'.format(ipp))
    soup_loader = SoupLoader(bot=True, use_proxies=True)

    ig = ReebokIg()
    parser = Parsing.BaseParser(get_offers_list=get_offers_list, get_item_dict=ig,
                                soup_loader=soup_loader)
    size_list = get_reebok_sizes_list(soup_loader=soup_loader)

    links = Parsing.sl_link_gen(baselinks=reebok_baselinks, sizes_list=size_list,
                                get_pg_lim=get_maxpage_func(ipp=ipp, soup_loader=soup_loader),
                                ipp=ipp)
    output(parser(links), "reebok")


class ReebokIg(ItemGetter):
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
        'get_additional_info',
        'get_utc',
    ]

    domain = 'https://www.reebok.pl/mezczyzni-buty'
    brand = 'reebok'

    def get_link(self, item, request):
        img = request['offer'].find('img', class_='show lazyload')
        a = img.parent
        link = a['href']
        link, _ = link.split('?')
        item['link'] = self.domain + link

    @staticmethod
    def get_colorway(item, request):
        item['colorway'] = get_colorway(request['offer'])

    def get_brand(self, item, request):
        item['brand'] = self.brand

    @staticmethod
    def get_name(item, request):
        item['name'] = get_name(request['offer'])

    def get_model(self, item, request):
        item['model'] = get_model(request['offer'], self.brand)

    @staticmethod
    def get_price(item, request):
        item['price'] = get_prices(request['offer'])

    def get_sizes(self, item, request):
        item['sizes'] = get_sizes(request['size'])

    @staticmethod
    def get_item_id(item, request):
        item['item_id'] = get_id(request['offer'])

    @staticmethod
    def get_img_link(item, request):
        item['img_link'] = get_img_link(request['offer'])

    @staticmethod
    def get_additional_info(item, request):
        item['additional_info'] = additional_info(request['offer'])


def get_sizes(size):
    db_sizes = []
    db_sizes.append('eu' + format_size_number(size))
    return db_sizes


def additional_info(offer):
    tags = []
    if offer.find('div', class_='badge new'):
        tags.append('new')
    if offer.find('div', class_='badge preview'):
        tags.append('soon')
    if tags:
        return {'tags': tags}
    return {}


def get_reebok_sizes_list(soup_loader):
    soup = soup_loader('https://www.reebok.pl/mezczyzni-buty')
    ul = soup.find(attrs={'data-filtername': 'sizeSearchValue'})
    lis = ul.find_all('li')[:-1]
    return [li.attrs['data-filtervalue'] for li in lis]


def get_maxpage_func(ipp, soup_loader):
    def get_maxpage(link, size):
        try:
            link = link.format(ipp=ipp, size=size, position=0)
            logger.info('Getting max page for baselink {} ...'.format(link))
            soup = soup_loader(link)
            li = soup.find('li', class_='paging-total')
            num = re.sub(r'\D', '', li.text)
            logger.info('Max page for base link {} is {}'.format(link, num))
            return int(num)
        except AttributeError:
            logger.exception('Probably, one page only found. Returning max page = 1')
            return 1
    return get_maxpage


@text_lower
@text_spaces_del
def get_name(offer):
    img = offer.find('img', class_='show lazyload')
    name = img.attrs['alt']
    name = name.replace('-', '', 1)
    name = name.replace('Buty', '')
    name = name.lower()
    return name


@text_lower
@text_spaces_del
def get_colorway(offer):
    img = offer.find('img', class_='show lazyload')
    colorway = img.attrs['alt'].replace(img.attrs['title'], '')
    item_id = get_id(offer)
    colorway = colorway.replace(item_id, '')

    return colorway


@text_lower
@text_spaces_del
def get_id(offer):
    div = offer.find('div', {'data-target': True})
    item_id = div.attrs['data-target']

    return item_id.lower()


def get_img_link(offer):
    img = offer.find('img', class_=re.compile('lazyload'))
    for attr in ('src', 'data-original',):
        imglink = img.attrs.get(attr)
        if imglink:
            return imglink


def get_prices(offer):
    price = offer.find('span', class_='salesprice').text
    price = re.sub('[^\d,]', '', price)
    price = price.replace(',', '.')
    price = float(price)
    return convert("PLN", "USD", price)


@text_lower
@text_spaces_del
def get_model(offer, brandname):
    img = offer.find('img', class_=re.compile('lazyload'))
    title = img.attrs['title']
    title = title.lower()
    title = title.replace(brandname, '')
    title = title.replace('-', '', 1)
    title = title.replace('shoes', '')
    return title.replace(get_id(offer), '')


def get_offers_list(soup):
    try:
        return soup.find_all('div', class_='product-tile')
    except:
        logging.error('Unable to locate offer elements')
        return []


if __name__ == '__main__':
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
        reebok_parse()
    else:
        logger.error('Scraping job cannot be started because'
                     ' job with the same name %r is not finished. ' % scraper_name)
