# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging

from elasticsearch.helpers import bulk

from dbhandling.indexing import es, update_script, EmptyBufferWriteException, \
    BufferOverflowException

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

    def __init__(self, conn=None, buffer_size=200, bulk=bulk):
        if conn is not None:
            self.conn = conn
        self.bulk = bulk
        self.default_buffer_size = buffer_size
        self.buffers = {}

    @classmethod
    def from_crawler(cls, crawler):
        s = crawler.settings
        return cls(buffer_size=s.getint('DB_BUFFER_SIZE', 200))

    def write_from_buffer(self, spider):
        buffer = self.buffers[spider.name]
        if buffer.is_empty():
            raise EmptyBufferWriteException("Unable to write"
                                            " from the buffer because"
                                            " it is empty.")
        items_batch = buffer.retrieve()
        return self._write(items_batch)

    def _write(self, items_batch):
        updates = (item.get_bulk_update_dict() for item in items_batch)
        return self.bulk(self.conn, updates)

    def process_item(self, item, spider):
        buffer = self.get_buffer(spider)
        buffer.add(item)
        if buffer.is_full():
            self.write_from_buffer(spider)

    def get_buffer(self, spider):
        if spider.name not in self.buffers:
            size = getattr(spider, 'buffer_size', self.default_buffer_size)
            buff = self.ItemsBuffer(size)
            self.buffers[spider.name] = buff
        return self.buffers[spider.name]

    def close_spider(self, spider):
        for buffer in self.buffers.values():
            if not buffer.is_empty():
                self.write_from_buffer(buffer)


class RunRepeatSesionedPipeline(KicksScraperPipeline):
    def write_from_buffer(self, spider):
        buff_size = self.get_buffer_size(spider)
        # logger.info(f'Writing batch to elasticsearch. Batch size: {buff_size}')
        result = super().write_from_buffer(spider)
        spider.session.update_status(buff_size)
        return result

    def get_buffer_size(self, spider):
        return len(self.buffers[spider.name])
