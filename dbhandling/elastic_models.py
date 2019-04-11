from elasticsearch import Elasticsearch
from elasticsearch_dsl import (Text, Document, Integer, Double, Keyword,
                               Boolean, MultiSearch)

client = Elasticsearch()

index_name = 'kicks_test'


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
    link = Text(
        analyzer='simple',
        fields={'keyword': Keyword()}
    )
    img_link = Text(
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

    @classmethod
    def batch_query(cls, searches):
        ms = MultiSearch(using=cls.Index.using,
                         index=cls.Index.name)
        print(searches)
        for s in searches:
            ms = ms.add(s)
        return ms.execute()

    @property
    def descr(self):
        return (self.name or
                (self.brand + self.model + self.colorway)).upper()

