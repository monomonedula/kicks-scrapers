import random
from time import time

import pytest

from .items import KicksScraperItem, RunRepeatItem, \
    SneakerItem, RRElastic
from test_utils.utils import Random


def test_kicks_scraper_item_to_elastic_id():
    data, _ = make_kicks_scraper_item_data()
    elastic_item = KicksScraperItem(**data).to_elastic()
    assert elastic_item.meta.id == data['id']


def test_kicks_scraper_item_to_elastic_fields():
    data_dict, elastic_fields = make_kicks_scraper_item_data()
    elastic_item = KicksScraperItem(**data_dict).to_elastic()
    assert all(
        (getattr(elastic_item, field) == data_dict[field]
         for field in elastic_fields)
    )


def make_kicks_scraper_item_data():
    rand = Random(time())
    data = {'id': rand.randint(1, 100000),
            'name': rand.random_string(40),
            'price': rand.randint(10, 200),
            'brand': rand.random_string(10),
            'sizes': list(rand.random_strings(10, 4)),
            'colorway': rand.random_string(10),
            'model': rand.random_string(10),
            'url': rand.random_string(40),
            'img_url': rand.random_string(50)}
    fields = list(data.keys())
    fields.remove('id')
    return data, fields


def test_runrepeat_item_to_elastic_id():
    data, _ = make_runrepeat_item_data()
    elastic_item = RunRepeatItem(**data).to_elastic()
    assert elastic_item.meta.id == data['id']


def test_runrepeat_item_to_elastic_fields():
    data_dict, elastic_fields = make_runrepeat_item_data()
    elastic_item = RunRepeatItem(**data_dict).to_elastic()
    assert all(
        (getattr(elastic_item, field) == data_dict[field]
         for field in elastic_fields)
    )


def make_runrepeat_item_data():
    rand = Random(time())
    data = {'id': rand.random_string(50),
            'name': rand.random_string(40),
            'brand': rand.random_string(10),
            'brand_slug': rand.random_string(10),
            'score': rand.randint(0, 100),
            'views': rand.randint(0, 5000),
            'categories': rand.random_strings_range((0, 3))}
    fields = list(data.keys())
    fields.remove('id')
    return data, fields
