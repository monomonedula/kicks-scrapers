import scrapy

from dbhandling.elastic_models import SneakerItem, RunRepeatItem as RRElastic


class KicksScraperItem(scrapy.Item):
    id = scrapy.Field()
    name = scrapy.Field()
    brand = scrapy.Field()
    model = scrapy.Field()
    colorway = scrapy.Field()
    price = scrapy.Field()
    sizes = scrapy.Field()
    item_id = scrapy.Field()
    url = scrapy.Field()
    img_url = scrapy.Field()

    def to_elastic(self):
        d = self.copy()
        del d['id']
        item = SneakerItem(**d)
        item.meta.id = self['id']
        return item


class RunRepeatItem(scrapy.Item):
    elastic_model = RRElastic

    id = scrapy.Field()
    name = scrapy.Field()
    brand = scrapy.Field()
    brand_slug = scrapy.Field()
    score = scrapy.Field()
    views = scrapy.Field()
    categories = scrapy.Field()

    @classmethod
    def from_runrepeat_json_dict(cls, data: dict, use_users_score=False):
        item = cls(id=data['slug'],
                   name=data['brand']['name'],
                   brand_slug=data['brand']['slug'],
                   views=data['views'],
                   score=data['score'],
                   categories=[c['slug'] for c in data['categories']])

        if use_users_score and item['score'] == 0:
            item['score'] = data['users_score']
        return item

    def to_elastic(self):
        d = self.copy()
        del d['id']
        item = self.elastic_model(**d)
        item.meta.id = self['id']
        return item
