import logging
import os

from pymongo import MongoClient
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


es = Elasticsearch(['http://localhost:9200/'])
mongo_client = MongoClient()
scraping = mongo_client.scraping

logger = logging.getLogger(__name__)

main_index_name = 'kicks'

this_directory_path = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(this_directory_path, 'update_script.painless')) as scr:
    update_script = scr.read()


class Writer:
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
            if self.is_full:
                raise BufferOverflowException('Unable to add item to buffer. Buffer is full')
            self.items[item.id] = item

        def retrieve(self):
            return [self.items.pop(key) for key in self.items]

    def __init__(self, scraper_name, conn, items, buffer_size=200):
        self.scraper_name = scraper_name
        self.conn = conn
        self.items_iter = items.__iter__()
        self.buff_size = buffer_size
        self.buffer = self.ItemsBuffer(buffer_size)

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

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

    @classmethod
    def write_items(cls, items, conn, scraper_name, buffer_size=200):
        with cls(scraper_name, conn, items, buffer_size) as writer:
            while writer.fill_buffer():
                writer.write_from_buffer()
            try:
                writer.write_from_buffer()
            except EmptyBufferWriteException:
                pass


class SizeLayerWriter(Writer):
    def write_from_buffer(self):
        pass



class BufferOverflowException(Exception):
    pass


class EmptyBufferWriteException(Exception):
    pass

