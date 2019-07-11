# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from dbhandling.indexing import es, update_script


class KicksScraperPipeline(object):
    def process_item(self, item, spider):
        return item


class RunRepeatPipeline:
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

    def write_from_buffer(self):
        if self.buffer.is_empty():
            raise EmptyBufferWriteException("Unable to write"
                                            " from the buffer because"
                                            " it is empty.")
        items_batch = self.buffer.retrieve()
        updates = (item.get_bulk_update_dict() for item in items_batch)
        return bulk(self.conn, updates)

    def process_item(self, item, spider):
        self.buffer.add(item)
        if self.buffer.is_full():
            self.write_from_buffer()


class RunRepeatSesionedPipeline(RunRepeatPipeline):
    pass