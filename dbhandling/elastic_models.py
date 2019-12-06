import os
import logging
from datetime import datetime, timezone

from elasticsearch import Elasticsearch
from elasticsearch_dsl import (
    Text,
    Document,
    Integer,
    Double,
    Keyword,
    Boolean,
    Float,
    Percolator,
    Search,
)

client = Elasticsearch()

index_name = "kicks"

logger = logging.getLogger(__name__)

this_directory_path = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(this_directory_path, "update_script.painless")) as scr:
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
    item_id = Text(fields={"keyword": Keyword()})
    url = Text(analyzer="simple", fields={"keyword": Keyword()}, required=True,)
    img_url = Text(analyzer="simple", fields={"keyword": Keyword()})
    telegram_img_id = Text(analyzer="simple", fields={"keyword": Keyword()})
    last_update = Double()

    new = Boolean()
    recommended = Boolean()
    recommended_price_diff = Integer()
    new_sizes = Keyword(multi=True)
    price_change = Integer()

    class Index:
        name = index_name
        using = client

    @property
    def descr(self):
        return (self.name or (self.brand + self.model + self.colorway)).upper()

    def get_bulk_update_dict(self):
        d = self.to_dict(include_meta=True)
        del d["_source"]
        d["_op_type"] = "update"
        d["script"] = self.get_update_script()
        d["upsert"] = self.get_upsert_dict()
        return d

    def get_update_script(self):
        return {
            "lang": "painless",
            "source": update_script,
            "params": {
                "sizes": list(self.sizes),
                "price": self.price,
                "new_update_time": get_time(),
                "img_url": self.img_url,
            },
        }

    def get_upd_dict(self):
        pass

    def get_upsert_dict(self):
        return {**self.to_dict(), "new": True}

    def to_dict(self, include_meta=False, skip_empty=True):
        # TODO: this may be inefficient on large document set,
        #       consider implementing bulk percolation mechanism
        data = super().to_dict(include_meta, skip_empty)
        s = (
            Search(index="test-percolator")
            .query(
                "percolate",
                field="query",
                index=self._get_index(),
                document=self.to_dict(),
            )
            .extra(min_score=0.15)
        )
        # min_score value may be adjusted or removed along with .extra call
        try:
            hit = max(s, key=lambda h: h.meta.score)
        except ValueError:
            pass
        else:
            data["recommended"] = True
            data["recommended_price_diff"] = data["price"] - hit.recommended_price
        return data


class RunRepeatItem(Document):
    class Index:
        name = "runrepeat"
        using = client

    name = Text()
    brand = Text()
    brand_slug = Keyword()
    score = Float()
    views = Integer()

    categories = Keyword(multi=True)

    def get_bulk_update_dict(self):
        d = self.to_dict(include_meta=True)
        d["_op_type"] = "update"
        d["doc"] = d.pop("_source")
        d["doc_as_upsert"] = True
        return d


class Recommendation(Document):
    class Index:
        name = "test-percolator"

    name = Text()
    brand = Text()
    model = Text()

    query = Percolator()
    recommended_price = Integer()

# recommendation example construction:
# Recommendation(
#     _id="1234",
#     recommended_price=100,
#     query=Q("query_string", "Adidas Gazelle", fields=["name", "brand", "model"])
# )
