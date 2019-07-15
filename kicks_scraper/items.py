# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy

from dbhandling.elastic_models import SneakerItem, RunRepeatItem as RRElastic, \
    RRRunning, RRSneaker, RRBasketballShoes, RRFootballShoes, RRTrainingShoes


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
        item.meta.id = self.id
        return item


class RunRepeatItem(scrapy.Item):
    elastic_model = RRElastic

    id = scrapy.Field()
    name = scrapy.Field()
    core_score = scrapy.Field()

    price = scrapy.Field()
    weight = scrapy.Field()
    top = scrapy.Field()    # low, mid, high

    top_most_popular = scrapy.Field()
    top_brand = scrapy.Field()
    top_overall = scrapy.Field()

    collection = scrapy.Field()

    def to_elastic(self):
        d = self.copy()
        del d['id']
        item = self.elastic_model(**d)
        item.meta.id = self.id
        return item


class RunRepeatSneaker(RunRepeatItem):
    elastic_model = RRSneaker

    inspired_from = scrapy.Field()


class RunRepeatRunning(RunRepeatItem):
    elastic_model = RRRunning

    terrain = scrapy.Field()
    arch_support = scrapy.Field()
    use = scrapy.Field()


class RunRepeatBasketballShoes(RunRepeatItem):
    elastic_model = RRBasketballShoes

    lockdown = scrapy.Field()


class RunRepeatFootballShoes(RunRepeatItem):
    elastic_model = RRFootballShoes

    surface = scrapy.Field()
    lacing = scrapy.Field()


class RunRepeatTrainingShoes(RunRepeatItem):
    elastic_model = RRTrainingShoes

    use = scrapy.Field()
    htt_drop = scrapy.Field()
    arch_support = scrapy.Field()

