# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class KicksScraperItem(scrapy.Item):
    name = scrapy.Field()
    brand = scrapy.Field()
    model = scrapy.Field()
    colorway = scrapy.Field()
    price = scrapy.Field()
    sizes = scrapy.Field()
    item_id = scrapy.Field()
    url = scrapy.Field()
    img_url = scrapy.Field()


class RunRepeatItem(scrapy.Item):
    name = scrapy.Field()
    corescore = scrapy.Field()
    shoe_type = scrapy.Field()

    price = scrapy.Field()
    weight = scrapy.Field()
    top = scrapy.Field()    # low, mid, high

    top_most_popular = scrapy.Field()
    top_brand = scrapy.Field()
    top_overall = scrapy.Field()

    collection = scrapy.Field()


class RunRepeatSneaker(RunRepeatItem):
    inspired_from = scrapy.Field()


class RunRepeatRunning(RunRepeatItem):
    terrain = scrapy.Field()
    arch_support = scrapy.Field()
    use = scrapy.Field()


class RunRepeatBasketballShoes(RunRepeatItem):
    lockdown = scrapy.Field()


class RunRepeatFootballShoes(RunRepeatItem):
    surface = scrapy.Field()
    lacing = scrapy.Field()


class RunRepeatTrainingShoes(RunRepeatItem):
    use = scrapy.Field()
    htt_drop = scrapy.Field()
    arch_support = scrapy.Field()

