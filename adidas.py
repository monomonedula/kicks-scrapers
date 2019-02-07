import logging
import re
import json

from fluent import asynchandler, handler

from dbhandling import parserdb
import Parsing
from basic_utils import text_lower, convert, format_size_number
from webutils.pageloader import LxmlSoupLoader
from itemgetter import ItemGetter

logger = logging.getLogger(__name__)


adidas_baselinks = [
    'https://www.adidas.pl/mezczyzni-buty?start={position}',
    'https://www.adidas.pl/kobiety-buty?start={position}',
]

scraper_name = 'adidas'


def adidas_parse(*, output=Parsing.database_writer, ipp=24):
    if ipp not in (120, 24):
        raise ValueError('Unknown items per page value: {}'.format(ipp))
    soup_loader = LxmlSoupLoader(bot=False, use_proxies=True)

    ig = AdidasIg(soup_loader=soup_loader)
    parser = Parsing.BaseParser(get_offers_list=get_offers_list,
                                get_item_dict=ig,
                                soup_loader=soup_loader)

    links = Parsing.links(baselinks=adidas_baselinks,
                          maxpage=get_maxpage_func(soup_loader, ipp),
                          ipp=ipp,
                          start_from=0)
    return output(parser(links), scraper_name)


class AdidasIg(ItemGetter):
    domain = 'https://www.adidas.pl/'
    brand = 'adidas'
    fields = [
        'get_link',
        'get_colorway',
        'get_brand',
        # 'get_name',
        'get_model',
        'get_price',
        'get_item_id',
        'get_sizes',
        'get_img_link',
        # 'get_additional_info',
        'get_utc',
    ]

    def get_link(self, item, request):
        print('GETTING LINK')
        item['link'] = ''.join((self.domain, get_relative_link(request['offer'])))

    def get_colorway(self, item, request):
        page = self.soup_loader(item['link'])
        item['colorway'] = get_colorway_from_page(page)

    @classmethod
    def get_brand(cls, item, request):
        item['brand'] = cls.brand

    @staticmethod
    def get_model(item, request):
        item['model'] = get_model(request['offer'])

    @staticmethod
    def get_price(item, request):
        item['price'] = get_price(request['offer'])

    @staticmethod
    def get_item_id(item, request):
        item['item_id'] = get_item_id(item['link'])

    def get_sizes(self, item, request):
        iid = item['item_id'].upper()
        link = 'https://www.adidas.pl/api/products/{}/availability'.format(iid)
        sizes_json_req = self.soup_loader.loadpage(link)
        item['sizes'] = get_sizes(sizes_json_req.text)


    @staticmethod
    def get_img_link(item, request):
        item['img_link'] = get_img_link(request['offer'])


def get_relative_link(offer):
    css_sel = 'div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > a:nth-child(1)'
    a_tag = offer.cssselect(css_sel)[0]
    return a_tag.attrib['href']


@text_lower
def get_colorway_from_page(page_lxml):
    return page_lxml.cssselect('div.gl-label--large:nth-child(2)')[0].text


@text_lower
def get_model(offer):
    model = offer.cssselect('div > div > div.gl-product-card__details > a > div.gl-product-card__details-main > '
                            'div.gl-product-card__name.gl-label.gl-label--medium')[0].attrib['title']
    return re.sub('buty', '', model, 1, re.IGNORECASE)


def get_price(offer):
    price = offer.cssselect('div > div > div.gl-product-card__details > a '
                            '> div.gl-product-card__details-main > div.gl-price-container > span')[0].text
    price = re.sub('\D', '', price)
    return convert("PLN", "USD", float(price))


def get_sizes(size_req_json):
    if isinstance(size_req_json, str):
        size_req_json = json.loads(size_req_json)
    elif not isinstance(size_req_json, dict):
        raise TypeError('Expected "str" or "dict" type, got %r' % type(size_req_json))

    sizes = []
    try:
        for i in size_req_json['variation_list']:
            if i['availability'] > 0:
                val = i['size']
                sizes.append('eu' + format_size_number(val))
    except KeyError:
        logger.debug('Key error in sizes api %s response. Returning no sizes.')
        return []
    return sizes


@text_lower
def get_item_id(link):
    print('Link %s '% link)
    _, iid = link.rsplit('/', 1)
    iid, _ = iid.split('.', 1)
    return iid


def get_img_link(offer):
    return offer.findall('.//img')[0].attrib['src']


def get_offers_list(page):
    return page.cssselect('#app > div > div.plp-page___1UWVZ > div > div:nth-child(2) > '
                          'div > div > div.col-s-12.col-l-18.no-gutters-s > '
                          'div.product-container___3GvlZ')[0].getchildren()


def get_maxpage_func(lxml_soup_loader, ipp=24):
    def maxpage(link):
        print('maxpage start')
        link = link.format(position=0)
        print('Loading link %s' % link)
        soup = lxml_soup_loader(link)
        print('soup type: ', type(soup))
        tag = soup.cssselect('.count___11uU6')[0]
        return 1 + int(re.sub('\D', '', tag.text)) // ipp
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

    if parserdb.is_finished(scraper_name):
        adidas_parse()
    else:
        logger.error('Scraping job cannot be started because'
                     ' job with the same name %r is not finished. ' % scraper_name)