from time import time

import pytest

from kicks_scraper.items import KicksScraperItem, RunRepeatItem
from test_utils.utils import Random


# TODO: replace random generated values with constant ones for better
#       test readability


def json_rr_dict():
    import os
    import json
    this_dir = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(this_dir, 'item_example.json')
    with open(path) as f:
        return (
            json.loads(f.read()),
            {
                'name': 'Jordan Heritage',
                'score': 98.812,
                'id': 'jordan-heritage',
                'brand': 'Jordan',
                'brand_slug': 'jordan',
                'views': 30,
                'categories': ['sneakers']
            }
        )


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


def test_runrepeat_item_from_json_dict():
    data, expected = json_rr_dict()
    item = RunRepeatItem.from_runrepeat_json_dict(data)
    assert all(
        (item[field] == expected[field]
         for field in expected)
    )


def test_runrepeat_item_to_elatic():
    data, elastic_fields = make_rr_item_data()
    elastic_item = RunRepeatItem(**data).to_elastic()
    assert all(
        (getattr(elastic_item, field) == data[field]
         for field in elastic_fields)
    )


def test_runrepeat_item_to_elastic_id():
    data, _ = make_rr_item_data()
    elastic_item = RunRepeatItem(**data).to_elastic()
    assert elastic_item.meta.id == data['id']


def make_rr_item_data():
    def random_string():
        return rand.random_string(rand.randint(5, 40))

    rand = Random(time())
    data = dict(id=random_string(),
                name=random_string(),
                brand=random_string(),
                brand_slug=random_string(),
                views=random_string(),
                score=float(rand.randint(0, 100)),
                categories=[random_string() for _ in range(2)])
    fields = list(data.keys())
    fields.remove('id')
    return data, fields


def make_kicks_scraper_item_data():
    rand = Random(time())
    url = rand.random_string(40)
    data = {'id': url,
            'name': rand.random_string(40),
            'price': rand.randint(10, 200),
            'brand': rand.random_string(10),
            'sizes': list(rand.random_strings(10, 4)),
            'colorway': rand.random_string(10),
            'model': rand.random_string(10),
            'url': url,
            'img_url': rand.random_string(50)}
    fields = list(data.keys())
    fields.remove('id')
    return data, fields


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
