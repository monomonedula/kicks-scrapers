# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging
from functools import partial

from elasticsearch.helpers import bulk
from typing import Dict

from dbhandling.indexing import es, EmptyBufferWriteException, \
    BufferOverflowException

logger = logging.getLogger(__name__)


class ItemsStorage:
    def __init__(self, bulk, buffers: Dict[str, "ItemsBuffer"] = None, buffer_size=200):
        self._buffers = buffers or {}
        self._bulk = bulk
        self._buff_size = buffer_size

    def add(self, item, key):
        buffer = self._buffers.setdefault(key, ItemsBuffer(self._buff_size))
        if buffer.is_full():
            updates = (item.get_bulk_update_dict() for item in buffer.retrieve())
            self._bulk(updates)
        buffer.add(item)

    def close(self):
        for buffer in self._buffers.values():
            if not buffer.is_empty():
                updates = (item.get_bulk_update_dict() for item in buffer.retrieve())
                self._bulk(updates)


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


class KicksScraperPipeline:
    def __init__(self, bulk, buffer_size=200):
        self._storage = ItemsStorage(bulk, buffer_size=buffer_size)

    @classmethod
    def from_crawler(cls, crawler):
        s = crawler.settings
        return cls(buffer_size=s.getint('DB_BUFFER_SIZE', 200),
                   bulk=partial(bulk, es))

    def process_item(self, item, spider):
        self._storage.add(item.to_elastic(), spider.name)

    def close_spider(self, spider):
        self._storage.close()
