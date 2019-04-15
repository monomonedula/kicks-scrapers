import os
import logging
from datetime import datetime, timezone

from elasticsearch import Elasticsearch
from elasticsearch_dsl import (Text, Document, Integer, Double, Keyword,
                               Boolean)

client = Elasticsearch()

index_name = 'kicks_test'

logger = logging.getLogger(__name__)

this_directory_path = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(this_directory_path, 'update_script.painless')) as scr:
    update_script = scr.read()


def get_time() -> float:
    return datetime.utcnow().replace(tzinfo=timezone.utc).timestamp()


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
    last_update = Double(default=get_time)

    new = Boolean()
    new_sizes = Keyword(multi=True)
    price_change = Integer()

    class Index:
        name = index_name
        using = client

    @property
    def descr(self):
        return (self.name or
                (self.brand + self.model + self.colorway)).upper()

    def get_bulk_update_dict(self):
        d = self.to_dict(include_meta=True)
        del d['_source']
        d['_op_type'] = 'update'
        d['script'] = self.get_update_script()
        d['upsert'] = self.get_upsert_dict()
        return d

    def get_update_script(self):
        return {
            'lang': 'painless',
            'source': update_script,
            'params': {
                'sizes': list(self.sizes),
                'price': self.price,
                'new_update_time': get_time(),
                'img_url': self.img_url,
            }
        }

    def get_upd_dict(self):
        pass

    def get_upsert_dict(self):
        d = self.to_dict()
        d['new'] = True
        return d
