import logging
import os

from pymongo import MongoClient
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from dbhandling.scr_session import ScrapingSession

es = Elasticsearch(['http://localhost:9200/'])
mongo_client = MongoClient()
scraping = mongo_client.scraping

logger = logging.getLogger(__name__)

this_directory_path = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(this_directory_path, 'update_script.painless')) as scr:
    update_script = scr.read()


class Writer:
    conn = es

    class ItemsBuffer:
        def __init__(self, max_size):
            self.max_size = max_size
            self.items = dict()

        def __len__(self):
            return len(self.items)

        def is_full(self):
            return len(self) >= self.max_size

        def is_empty(self):
            return len(self) == 0

        def add(self, item):
            if self.is_full():
                raise BufferOverflowException('Unable to add item to buffer. Buffer is full')
            self.items[item.meta.id] = item

        def retrieve(self):
            items = list(self.items.values())
            self.items = {}
            return items

    def __init__(self, scraper_name, items, conn=None, buffer_size=200):
        self.scraper_name = scraper_name
        if conn is not None:
            self.conn = conn
        self.items_iter = items.__iter__()
        self.buff_size = buffer_size
        self.buffer = self.ItemsBuffer(buffer_size)

    def fill_buffer(self):
        for item in self.items_iter:
            if not self.buffer.is_full():
                self.buffer.add(item)
            else:
                return True
        return False

    def write_from_buffer(self):
        if self.buffer.is_empty():
            raise EmptyBufferWriteException("Unable to write"
                                            " from the buffer because"
                                            " it is empty.")
        items_batch = self.buffer.retrieve()
        updates = (item.get_bulk_update_dict() for item in items_batch)
        return bulk(self.conn, updates)

    def write_items(self):
        while self.fill_buffer():
            self.write_from_buffer()
        try:
            self.write_from_buffer()
        except EmptyBufferWriteException:
            pass


class SizeLayerWriter(Writer):
    class ItemsBuffer(Writer.ItemsBuffer):
        def is_full(self):
            return False

        def add(self, item):
            if item.meta.id in self.items:
                old_item = self.items[item.meta.id]
                # no sets are used for merging here
                # because it is expected that the
                # new item has only
                # one or few sizes
                for s in item.sizes:
                    if s not in old_item.sizes:
                        old_item.sizes.append(s)
            else:
                self.items[item.meta.id] = item

    def __init__(self, scraper_name, items, conn=None):
        super().__init__(scraper_name=scraper_name,
                         conn=conn,
                         items=items,
                         buffer_size=-1)


class SessionedWriter(Writer):
    def __init__(self, scraper_name,
                 items, conn=None, buffer_size=200,
                 allow_concurrent_sessions=False):
        self.allow_concurrent_sessions = allow_concurrent_sessions
        self.session = None
        self.written_count = 0
        super().__init__(scraper_name=scraper_name,
                         conn=conn,
                         items=items,
                         buffer_size=buffer_size)

    def write_items(self):
        self.session = ScrapingSession.open_new_session(self.scraper_name,
                                                        self.allow_concurrent_sessions)
        with self.session:
            super().write_items()

    def write_from_buffer(self):
        logger.info('Writing batch to elasticsearch.'
                    ' Batch size: %s, session id: %s' % (len(self.buffer),
                                                         self.session.id))
        buffer_size = len(self.buffer)
        res = super().write_from_buffer()
        self.written_count += buffer_size
        self.session.update_status(self.written_count)
        return res


class SessionedSizeLayerWriter(SizeLayerWriter):
    def __init__(self, scraper_name,
                 items, conn=None, allow_concurrent_sessions=False):
        self.allow_concurrent_sessions = allow_concurrent_sessions
        self.session = None
        self.written_count = 0
        super().__init__(scraper_name=scraper_name,
                         conn=conn,
                         items=items)

    def write_items(self):
        self.session = ScrapingSession.open_new_session(self.scraper_name,
                                                        self.allow_concurrent_sessions)
        with self.session:
            super().write_items()
            logger.info('Closing scraping session %s. Total items obtained: %s' % (self.session.id,
                                                                                   self.written_count))

    def write_from_buffer(self):
        logger.info('Writing batch to elasticsearch.'
                    ' Batch size: %s, session id: %s' % (len(self.buffer),
                                                         self.session.id))
        buffer_size = len(self.buffer)
        res = super().write_from_buffer()
        self.written_count += buffer_size
        self.session.update_status(self.written_count)
        return res


class BufferOverflowException(Exception):
    pass


class EmptyBufferWriteException(Exception):
    pass
