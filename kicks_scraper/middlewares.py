# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from rotating_proxies.middlewares import RotatingProxyMiddleware as RPMd
from rotating_proxies.expire import Proxies,\
    extract_proxy_hostport

from webutils.get_proxies import get_proxies_list


class NeverEndingProxies(Proxies):
    def __init__(self, backoff=None):
        super().__init__(self.load_proxies(), backoff)

    @staticmethod
    def load_proxies():
        pl = get_proxies_list()
        return [f'http://{adress}:{port}' for adress, port in pl]

    def reset(self):
        for proxy in self.load_proxies():
            self.dead.discard(proxy)
            self.unchecked.add(proxy)
            self.proxies_by_hostport[extract_proxy_hostport(proxy)] = proxy


class RotatingProxyMiddleware(RPMd):

    def __init__(self, logstats_interval,
                 max_proxies_to_try, backoff_base, backoff_cap, crawler):
        super().__init__(
            proxy_list=[],
            logstats_interval=logstats_interval,
            stop_if_no_proxies=False,
            max_proxies_to_try=max_proxies_to_try,
            backoff_base=backoff_base,
            backoff_cap=backoff_cap,
            crawler=crawler,
        )
        # TODO: make some more elegant replacement of 'Proxies' class than this
        self.proxies = NeverEndingProxies(backoff=self.proxies.backoff)

    @classmethod
    def from_crawler(cls, crawler):
        s = crawler.settings
        mw = cls(
            logstats_interval=s.getfloat('ROTATING_PROXY_LOGSTATS_INTERVAL', 30),
            max_proxies_to_try=s.getint('ROTATING_PROXY_PAGE_RETRY_TIMES', 5),
            backoff_base=s.getfloat('ROTATING_PROXY_BACKOFF_BASE', 300),
            backoff_cap=s.getfloat('ROTATING_PROXY_BACKOFF_CAP', 3600),
            crawler=crawler,
        )
        crawler.signals.connect(mw.engine_started,
                                signal=signals.engine_started)
        crawler.signals.connect(mw.engine_stopped,
                                signal=signals.engine_stopped)
        return mw
