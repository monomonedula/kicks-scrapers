import threading
import logging

from fluent import asynchandler, handler

from Parsing import *

parsers = {
    'adidas': adidas_s,
    'reebok': reebok_parse,
    'chmielna20': chmielna20_parse,
    'supersklep': supersklep_parse,
    'mandmdirect': mandmdirect_parse,
    'worldbox': worldbox_parse,
    'sportsdirect': sportsdirect_parse,
    'sizeer': sizeer_parse,
    'distance': distance_scrape,
}


def crawl_sites(*sites):
    threads = [threading.Thread(target=parsers[site], name=site) for site in sites]
    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == '__main__':
    log_format = {
        'where': '%(module)s.%(funcName)s',
        'type': '%(levelname)s',
        'stack_trace': '%(exc_text)s',
    }

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('')
    logger.setLevel(level=logging.INFO)
    h = asynchandler.FluentHandler('kicks.scraper', host='localhost', port=24224)
    h.setLevel(level=logging.INFO)
    formatter = handler.FluentRecordFormatter(log_format)
    h.setFormatter(formatter)
    logging.getLogger('').addHandler(h)


    # chmielna20_parse() # ok
    # sizeer_parse() #ok
    # mandmdirect_parse() #ok
    # adidas_parse() # not ok
    # zalando_scrape() # ok
    # crawl_sites(*parsers.keys())
    # worldbox_parse() # ok
    distance_scrape()
