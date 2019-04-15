from time import sleep
import logging
import gc


logger = logging.getLogger(__name__)


class TooManyErrors(Exception):
    pass


class BaseScraper:
    def __init__(self, *, get_offers_list, get_item_dict,
                 driver_wrapper=None, soup_loader=None,
                 min_sleep_time=2.0):
        self.sleep_time = min_sleep_time
        self.get_offers_list = get_offers_list
        self.get_item_dict = get_item_dict
        self.driver_wrapper = driver_wrapper
        self.soup_loader = soup_loader or driver_wrapper.load_soup
        if not self.driver_wrapper and not self.soup_loader:
            raise ValueError('Neither driver_wrapper nor soup_loader are given')
        self.exceptions_counter = 0
        self.items_gathered = 0

    def __call__(self, links, maxpage=None):
        for i, data in enumerate(links):
            link = data.pop('link')
            if maxpage and i > maxpage:
                logger.info('Reached max page limit.')
                break
            sleep(self.sleep_time)
            logger.info('Loading %s' % link)
            bs_obj = self.soup_loader(link)
            logger.info('Parsing page {} ...'.format(link))
            for item in self._parse_page(bs_obj, page_data=data):
                yield item
            gc.collect()

    def _parse_page(self, bs_obj, page_data):
        for offer in self.get_offers_list(bs_obj):
            self.items_gathered += 1
            try:
                request = {'offer': offer, **page_data}
                item = self.get_item_dict(request=request)
            except Exception:
                logger.exception(page_data)
                self.exceptions_counter += 1
                if self.too_many_errors():
                    raise TooManyErrors("items total: %s , exceptions: %s" % (self.items_gathered,
                                                                              self.exceptions_counter))
            else:
                if item:
                    yield item

    def too_many_errors(self):
        return self.exceptions_counter / self.items_gathered > 0.5 and self.items_gathered > 100


def sl_link_gen(*, baselinks, sizes_list, get_pg_lim, ipp=None):
    for l in baselinks:
        for s in sizes_list:
            pg_lim = get_pg_lim(link=l, size=s)
            for p in range(pg_lim):
                if ipp:
                    yield {'link': l.format(position=ipp*p, size=s, ipp=ipp), 'size': s}
                else:
                    yield {'link': l.format(position=p, size=s), 'size': s}


def links(baselinks, maxpage, page_lim=None, ipp=None, start_from=1):
    for link in baselinks:
        mxpg = maxpage(link=link)
        for j in range(start_from, mxpg + 1):
            if page_lim and j > page_lim:
                return
            if ipp:
                yield {'link': link.format(position=j*ipp)}
            else:
                yield {'link': link.format(position=j)}
