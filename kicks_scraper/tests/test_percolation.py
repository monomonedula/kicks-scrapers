from time import sleep

import pytest

from elasticsearch import Elasticsearch
from elasticsearch_dsl import connections, Q

from dbhandling.elastic_models import SneakerItem, Recommendation


class Sneaker(SneakerItem):
    class Index:
        name = "kicks_test_telebot"

    percolators_index = "test_recommendations"


class TestRecommendation(Recommendation):
    class Index:
        name = "test_recommendations"


@pytest.fixture()
def es(pgsql):
    conn = connections.create_connection(hosts=["localhost"], timeout=20)
    index = "kicks_test_telebot"
    Sneaker.init(index=index, using=conn)
    es = Elasticsearch()
    populate(es, conn, index)
    yield es
    clean_up_es(es, index)


def populate(es, using, index):
    Sneaker(
        name="nike air test", price=100, sizes=["eu44", "eu44.5"], url="nike-air-test"
    ).save(using=using, index=index)
    Sneaker(
        name="nike air force 1",
        price=150,
        sizes=["eu41", "eu37.5"],
        url="nike-air-force-1",
    ).save(using=using, index=index)
    Sneaker(
        name="nike test 2", price=65, sizes=["eu40", "eu44.7"], url="nike-test-2"
    ).save(using=using, index=index)
    Sneaker(
        name="Nike court",
        price=130,
        sizes=["eu43", "eu44.3"],
        url="nike-court",
        new=True,
        recommended=True,
        recommended_price_diff=-30,
    ).save(using=using, index=index)
    Sneaker(
        name="Adidas Campus",
        price=76,
        sizes=["eu35", "eu38", "eu40"],
        url="adidas-campus-blabla",
        img_url="adidas-campus.jpg",
        recommended=True,
        recommended_price_diff=-10,
    ).save(using=using, index=index)
    Sneaker(
        name="Adidas Gazelle Black",
        price=78,
        sizes=["eu35", "eu36", "eu37"],
        url="adidas-gazelle-black",
        img_url="adidas-gazelle-black.jpg",
        new=True,
        recommended=True,
        recommended_price_diff=-20,
    ).save(using=using, index=index)
    Sneaker(
        name="Adidas spezial",
        price=80,
        img_url="adidas-spezial.jpg",
        sizes=["eu43.3"],
        url="adidas-spezial-grey",
        new=True,
    ).save(using=using, index=index)
    Sneaker(
        name="Adidas Spezial",
        price=91,
        sizes=["eu44", "eu45", "eu44.5"],
        url="adidas-spezial2.jpg",
        new_sizes=["eu45"],
    ).save(using=using, index=index)
    Sneaker(
        name="Puma suede",
        price=60,
        sizes=["eu40", "eu41"],
        url="puma-suede",
        price_change=-25,
    ).save(using=using, index=index)
    es.indices.flush(index=index)
    sleep(2)


def clean_up_es(es, *indices):
    for i in indices:
        es.indices.delete(index=i)


@pytest.fixture()
def perc_fixture():
    conn = connections.create_connection(hosts=["localhost"], timeout=20)
    Sneaker.init(index="kicks_test_telebot", using=conn)
    TestRecommendation.init(index="test_recommendations", using=conn)
    es = Elasticsearch()
    yield es
    clean_up_es(es, "test_recommendations", "kicks_test_telebot")


def test_save_doc(perc_fixture):
    es = perc_fixture
    TestRecommendation(
        _id="1234567",
        recommended_price=100,
        query=Q("query_string", query="Adidas Gazelle", fields=["name", "brand", "model"])
    ).save()
    TestRecommendation(
        _id="42",
        recommended_price=120,
        query=Q("query_string", query="Nike Air Force 1", fields=["name", "brand", "model"])
    ).save()
    es.indices.flush()
    sleep(1)
    item_dict = Sneaker(
        name="Adidas Gazelle Black",
        price=78,
        sizes=["eu35", "eu36", "eu37"],
        url="adidas-gazelle-black",
        img_url="adidas-gazelle-black.jpg",
    ).to_dict()
    assert item_dict["recommended"] is True
    assert item_dict["recommended_price_diff"] == -22
