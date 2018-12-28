import logging
from datetime import datetime
import uuid
import os

from pymongo import MongoClient
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from elasticsearch.exceptions import NotFoundError

from basic_utils.decorators import non_blocking


es = Elasticsearch(['http://localhost:9200/'])
mongo_client = MongoClient()
scraping = mongo_client.scraping

logger = logging.getLogger(__name__)

main_index_name = 'kicks'


def write_tmp(items, index, id_field='link'):
    def bulk_gen():
        for item in items:
            yield {
                '_type':
                    'shoes',
                '_op_type':
                    'update',
                '_id':
                    item[id_field],
                '_index':
                    index,
                'script': {
                    'source': "ctx._source.sizes.addAll(params.sizes); ctx._source.price = params.price",
                    'lang': 'painless',
                    'params': {
                        'price': item['price'],
                        'sizes': item['sizes'],
                    }
                },
                'upsert':
                    item,
            }
    return bulk(es, bulk_gen())


def commit(tmp_index_name, scroll_time='1m', batch_size=500):
    def batches():
        r = es.search(index=tmp_index_name, scroll=scroll_time,
                     size=batch_size)
        scroll_id = r['_scroll_id']
        hits = r['hits']['hits']
        while len(hits):
            yield hits
            r = es.scroll(scroll_id=scroll_id, scroll=scroll_time)
            scroll_id = r['_scroll_id']
            hits = r['hits']['hits']
        try:
            es.clear_scroll(scroll_id=scroll_id)
        except NotFoundError:
            pass

    for b in batches():
        write_hits_batch_to_index(batch=b, index_name=main_index_name)


@non_blocking
def write_hits_batch_to_index(batch, index_name=main_index_name):
    bulk(es, gendata(batch, index_name))


def write_docs_batch_to_index(batch, id_field='link', index_name=main_index_name, doc_type='shoes'):
    docs = ({'_source':
                 d,
             '_id':
                 d[id_field],
             '_type':
                 doc_type} for d in batch)
    bulk(es, gendata(docs, index_name))


def gendata(batch, index_name):
    for hit in batch:
        yield {
            "_index":
                index_name,
            "_type":
                hit['_type'],
            "_id":
                hit["_id"],
            '_op_type':
                'update',
            'script': {
                'lang': 'painless',
                'source': "ctx._source.new_sizes = [];"
                          ""
                          "for(int i = 0; i < params.sizes.length; i++){"
                          "    if (!ctx._source.sizes.contains(params.sizes[i])){"
                          "         ctx._source.new_sizes.add(params.sizes[i]);"
                          "     }"
                          "}"
                          "ctx._source.sizes = params.sizes;"
                          "if((params.new_update_time - 3600) > ctx._source.last_update){"
                          "     ctx._source.price_change = params.price - ctx._source.price;"
                          "}"
                          "ctx._source.price = params.price;"
                          "ctx._source.last_update = params.new_update_time;"
                          "ctx._source.img_link = params.img_link;",
                'params': {
                    'sizes': hit['_source']['sizes'],
                    'price': hit['_source']['price'],
                    'new_update_time': hit['_source']['last_update'],
                    'img_link': hit['_source']['img_link'],
                }
            },
            'upsert':
                hit['_source'],
        }


def new_tmp_scrape_session(scraper_name):
    ssid = uuid.uuid1()
    es_tmp_index = 'tmp-' + ssid.hex
    scraping.scr_sessions.insert_one({
        'session_id': ssid.hex,
        'start_time': datetime.utcnow(),
        'open': True,
        'last_activity': datetime.utcnow(),
        'scraper': scraper_name,
        'tmp_es_index_name': es_tmp_index,
    })
    es.indices.create(index=es_tmp_index)
    return es_tmp_index, ssid.hex


def new_scrape_session(scraper_name):
    ssid = uuid.uuid1()

    scraping.scr_sessions.insert_one({
        'session_id': ssid.hex,
        'start_time': datetime.utcnow(),
        'open': True,
        'last_activity': datetime.utcnow(),
        'scraper': scraper_name,
        'pid': os.getpid(),
        'documents_count': 0,
    })
    return ssid.hex


def scrape_session_still_open(session_id, documents_count):
    scraping.scr_sessions.update_one({
      'session_id': session_id,
    },
    {
        '$set': {
            'last_activity':
                datetime.utcnow(),
            'documents_count':
                documents_count,
        }
    })


def scrape_session_mark_closed(session_id):
    scraping.scr_sessions.update_one({
        'session_id': session_id,
    },
    {
        '$set': {
            'open': False,
            'termination_time': datetime.utcnow(),
        }
    })


def drop_index(index_name):
    return es.indices.delete(index=index_name)


def is_finished(scraper_name):
    s = scraping.scr_sessions.find_one({
        'scraper': scraper_name,
        'open': True,
        'ok': True,
    })
    return not s


def critical_session_exit(session_id):
    scraping.scr_sessions.update_one({
        'session_id': session_id,
    }, {
        '$set': {
            'ok': False,
            'open': False,
            'termination_time': datetime.utcnow(),
        }
    })