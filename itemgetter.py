import logging
from datetime import datetime, timezone
from time import sleep

logger = logging.getLogger(__name__)


class ItemGetter:
    fields = []

    def __init__(self, soup_loader=None):
        self.soup_loader = soup_loader
        self._page_cache = (None, None)

    def __call__(self, request):
        item = {}
        try:
            for method_name in self.fields:
                self.__getattribute__(method_name)(item, request)
            return item
        except Exception as e:
            self.exception_handler(e, item)

    @staticmethod
    def exception_handler(e, item):
        try:
            logger.error("Error occurred while parsing item with link {}.".format(item['link']))
        except KeyError:
            logger.error("Error occured. (Link to the item could not provided)")
        raise e

    @staticmethod
    def get_utc(item, request):
        item['last_update'] = datetime.utcnow().replace(tzinfo=timezone.utc).timestamp()

    def _load_page(self, link):
        sleep(0.4)
        self._page_cache = (self.soup_loader(link), link)

    def _get_page(self, link):
        if link != self._page_cache[1]:
            self._load_page(link)
        return self._page_cache[0]
