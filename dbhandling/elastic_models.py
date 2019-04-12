import os
import re
import logging

from elasticsearch import Elasticsearch
from elasticsearch_dsl import (Text, Document, Integer, Double, Keyword,
                               Boolean, MultiSearch)

client = Elasticsearch()

index_name = 'kicks_test'

logger = logging.getLogger(__name__)

this_directory_path = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(this_directory_path, 'update_script.painless')) as scr:
    update_script = scr.read()


class SneakerItem(Document):
    price = Integer(required=True)
    sizes = Keyword(multi=True)
    name = Text()
    brand = Text()
    model = Text()
    colorway = Text()
    item_id = Text(
        fields={'keyword': Keyword()}
    )
    url = Text(
        analyzer='simple',
        fields={'keyword': Keyword()},
        required=True
    )
    img_url = Text(
        analyzer='simple',
        fields={'keyword': Keyword()}
    )
    last_update = Double()

    new = Boolean()
    new_sizes = Keyword(multi=True)
    price_change = Integer()

    sl = Boolean()

    class Index:
        name = index_name
        using = client

    @property
    def descr(self):
        return (self.name or
                (self.brand + self.model + self.colorway)).upper()

    def get_bulk_update_dict(self):
        d = self.to_dict(include_meta=True)
        d['_op_type'] = 'update'
        d['script'] = self.get_update_script()
        d['upsert'] = self.get_upsert_dict()
        return d

    def get_update_script(self):
        return {
            'lang': 'painless',
            'source': update_script,
            'params': {
                'sizes': self.sizes,
                'price': self.price,
                'new_update_time': self.last_update,
                'img_link': self.img_url,
            }
        }

    def get_upd_dict(self):
        pass

    def get_upsert_dict(self):
        d = self.to_dict()
        d['new'] = True
        return d


class SneakerItemURLid(SneakerItem):
    def __init__(self, meta=None, **kwargs):
        if 'url' in kwargs:
            if meta is None:
                meta = {}
            meta['id'] = minimize_link(kwargs['url'])
        super().__init__(meta, **kwargs)


class SneakerItemSL(SneakerItemURLid):
    def get_bulk_tmp_update_dict(self):
        d = self.to_dict(include_meta=True)
        d['_op_type'] = 'update'
        d['script'] = self.get_tmp_update_script()
        d['upsert'] = self.get_upsert_dict()
        return d

    def get_tmp_update_script(self):
        return {
           'source': "ctx._source.sizes.addAll(params.sizes); ctx._source.price = params.price",
           'lang': 'painless',
           'params': {
               'price': self.price,
               'sizes': self.sizes,
           }
        }


def minimize_link(link):
    pattern = re.compile(r"https?://(www\.)?")
    return pattern.sub('', link).strip().strip('/')
