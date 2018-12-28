import re
import logging
from string import punctuation

from bs4 import Tag

import Parsing
from itemgetter import ItemGetter
from webutils import CachedTranslator
from webutils.pageloader import SoupLoader
from basic_utils import (contains_color, text_lower, text_spaces_del, convert,
                         identify_brand, format_size_number)


baselinks = [
    'https://chmielna20.pl/products/obuwie-mezczyzna-34eu/category,2/gender,M/size,{}/sizetype,EU/sort,1/page,{}',
    'https://chmielna20.pl/products/obuwie-kobieta-36eu/category,2/gender,W/size,{}/sizetype,EU/sort,1/page,{}',
]

translator = CachedTranslator()

logger = logging.getLogger(__name__)

punctuation_cleaner = str.maketrans(punctuation, ' ' * len(punctuation))


def chmielna20_parse(output=Parsing.database_size_layer_writer):
    soup_loader = SoupLoader(bot=True)
    cg = ChmielnaIg(soup_loader)
    parser = Parsing.BaseParser(get_offers_list=get_offers_list,
                                get_item_dict=cg,
                                soup_loader=soup_loader)
    link_gen = links(baselinks, soup_loader=soup_loader)
    item_gen = parser(link_gen)
    return output(item_gen, scraper_name="chmielna20")


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

    # def get_colorway(self, item, request):
    #     item['colorway'] = get_colorway(self.soup_loader, item['link'])

    @staticmethod
    def get_name(item, request):
        offer = request['offer']
        # item['name'] = get_name(offer) + ' ' + item['colorway']
        item['name'] = get_name(offer)

    @staticmethod
    def get_brand(item, request):
        item['brand'] = get_brand(request['offer'])

    # @staticmethod
    # def get_model(item, request):
    #     item['model'] = get_model(request['offer'], item['brand'])

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
def get_brand(offer):
    brand = identify_brand(get_name(offer))
    return brand if brand else ''


@text_lower
@text_spaces_del
def get_colorway(soup_loader, link):
    soup = soup_loader(link)
    colorway = _find_colorway(soup)
    if colorway:
        return colorway  # to remove "-" from the beginning of the string
    else:
        return ''


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


# @text_lower
# @text_spaces_del
# def get_model(offer, brand):
#     name = get_name(offer)
#     if brand in name:
#         name = name.replace(brand, '')
#     else:
#         brand_substring = get_brand_substring(name=name, brand=brand)
#         if brand_substring:
#             _, name = name.split(get_brand_substring(name=name, brand=brand), maxsplit=1)
#         else:
#             logger.warning('Unable to recognize brand in name "{}"'.format(name))
#             return ''
#
#     if '(' in name:
#         name, _ = name.split('(')
#
#     if '"' in name:
#         name, _ = name.split('"', maxsplit=1)
#
#     return name


def _find_colorway(soup):
    colorway = soup.find('div', class_='col-md-12 product__description active')
    if not colorway.children:
        return None

    children = [str(c.text) for c in colorway.children if type(c) is Tag and re.search('\w', c.text)]
    if len(children) < 2:
        return None
    else:
        return _most_suitable(children)


def _most_suitable(strings):
    best_st, best_weight = max(((string, _colorway_check(string)) for string in strings), key=lambda sv: sv[1])
    if best_weight < 0.5:
        return None
    else:
        best_st = re.sub('^\s*-', '', best_st)
        if '/' in best_st:
            best_st = best_st.split('/')
            best_st = (translator.translate(s, src='pl').text for s in best_st)
            best_st = '/'.join(best_st)
            return best_st
        else:
            return translator.translate(best_st, src='pl').text


def _colorway_check(line):
    res = 0.0
    if len(line) > 40:
        return res
    elif re.search('Lato \d\d\d\d|Jesień \d\d\d\d|Zima \d\d\d\d|Wiosna \d\d\d\d', line, re.IGNORECASE):
        return res

    res += 0.25 * line.count('/')
    line = ' '.join((s for s in line.split() if len(s) > 2))
    res += contains_color(translator.translate(line, src='pl').text)
    return res


if __name__ == '__main__':
    logging.basicConfig(format='[time: %(asctime)s] - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG,
                        filename='/home/vladislav/kicksproject/logs/test.log',
                        filemode='w')

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    chmielna20_parse()
