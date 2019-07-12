# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging

from elasticsearch.helpers import bulk

from dbhandling.indexing import es, update_script, EmptyBufferWriteException, \
    BufferOverflowException
from dbhandling.scr_session import ScrapingSession

logger = logging.getLogger(__name__)


class KicksScraperPipeline:
    conn = es

    class ItemsBuffer:
        def __init__(self, max_size):
            self.max_size = max_size
            self._items = dict()

        def __len__(self):
            return len(self._items)

        def is_full(self):
            return len(self) >= self.max_size

        def is_empty(self):
            return len(self) == 0

        def add(self, item):
            if self.is_full():
                raise BufferOverflowException('Unable to add item to buffer.'
                                              ' Buffer is full')
            self._items[item.meta.id] = item

        def retrieve(self):
            items = list(self._items.values())
            self._items = {}
            return items

    def __init__(self, conn=None, buffer_size=200):
        if conn is not None:
            self.conn = conn
        self.buff_size = buffer_size
        self.default_buffer_size = buffer_size
        self.buffers = {}

    @classmethod
    def from_crawler(cls, crawler):
        s = crawler.settings
        return cls(buffer_size=s.getint('DB_BUFFER_SIZE', 200))

    def write_from_buffer(self):
        if self.buffer.is_empty():
            raise EmptyBufferWriteException("Unable to write"
                                            " from the buffer because"
                                            " it is empty.")
        items_batch = self.buffer.retrieve()
        return self._write(items_batch)

    def _write(self, items_batch):
        updates = (item.get_bulk_update_dict() for item in items_batch)
        return bulk(self.conn, updates)

    def process_item(self, item, spider):
        buffer = self.get_buffer(spider)
        buffer.add(item)
        if buffer.is_full():
            self.write_from_buffer()

    def get_buffer(self, spider):
        if spider.name not in self.buffers:
            size = getattr(spider, 'buffer_size', self.default_buffer_size)
            buff = self.ItemsBuffer(size)
            self.buffers[spider.name] = buff
        return self.buffers[spider.name]

    def close_spider(self, spider):
        if not self.buffer.is_empty():
            self.write_from_buffer()


class RunRepeatSesionedPipeline(KicksScraperPipeline):
    class ItemsBuffer(KicksScraperPipeline.ItemsBuffer):
        # TODO: separate subbuffer for every spider session
        def __init__(self, max_size):
            self.max_size = max_size
            self._items = dict()

        def __len__(self):
            return len(self._items)

        def is_full(self):
            return len(self) >= self.max_size

        def is_empty(self):
            return len(self) == 0

        def add(self, item, spider_name=None):
            if self.is_full():
                raise BufferOverflowException('Unable to add item to buffer.'
                                              ' Buffer is full')
            self._items[item.meta.id] = item

        def retrieve(self):
            items = list(self._items.values())
            self._items = {}
            return items

    def __init__(self, conn=None, buffer_size=300,
                 allow_concurrent_sessions=False):
        self.allow_concurrent_sessions = allow_concurrent_sessions
        self.sessions = {}
        super().__init__(conn=conn,
                         buffer_size=buffer_size)

    @classmethod
    def from_crawler(cls, crawler):
        s = crawler.settings
        buffer_size = s.getint('DB_BUFFER_SIZE', 300)
        alcs = s.getbool('ALLOW_CONCURRENT', False)
        return cls(buffer_size=buffer_size,
                   allow_concurrent_sessions=alcs)

    def process_item(self, item, spider):
        self.buffer[spider.name].add(item)
        if self.buffer[spider.name].is_full(spider):
            self.write_from_buffer(spider)

    def write_from_buffer(self, spider=None):
        logger.info('Writing batch to elasticsearch.'
                    ' Batch size: %s' % (len(self.buffer)))
        if spider:
            buffer_size = len(self.buffer[spider.name])
            spider.session.update_status(self.buff_size)
            # TODO: write to the stats count  of written items

            items_batch = self.buffer[spider.name].retrieve()
            return self._write(items_batch)
        else:
            return super().write_from_buffer()
        # TODO: move main session handling to corresponding spider
