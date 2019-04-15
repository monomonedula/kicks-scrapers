import logging
import re

from dbhandling.elastic_models import SneakerItem, get_time
from time import sleep

logger = logging.getLogger(__name__)


class ItemGetter:
    fields = []

    def __init__(self, soup_loader=None):
        self.soup_loader = soup_loader
        self._page_cache = (None, None)

    def __call__(self, request):
        item = self.new_item()
        try:
            for method_name in self.fields:
                self.__getattribute__(method_name)(item, request)
            return item
        except Exception as e:
            self.exception_handler(e, item)

    @staticmethod
    def new_item():
        return SneakerItem()

    @staticmethod
    def exception_handler(e, item):
        try:
            logger.error("Error occurred while parsing item with link {}.".format(item['url']))
        except KeyError:
            logger.error("Error occured. (url to the item could not be  provided)")
        raise e

    def _load_page(self, link):
        sleep(0.4)
        self._page_cache = (self.soup_loader(link), link)

    def _get_page(self, link):
        if link != self._page_cache[1]:
            self._load_page(link)
        return self._page_cache[0]


class LinkIdentifiedItemGetter(ItemGetter):
    def __call__(self, request):
        item = super().__call__(request)
        item.meta.id = self.minimize_link(item.url)
        item.last_update = get_time()
        return item

    @staticmethod
    def minimize_link(link):
        pattern = re.compile(r"https?://(www\.)?")
        return pattern.sub('', link).strip().strip('/')
