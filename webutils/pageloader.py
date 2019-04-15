import logging
from socket import timeout

from requests_futures.sessions import FuturesSession
from bs4 import BeautifulSoup
from lxml.html.soupparser import fromstring
import requests

from webutils.smart_proxy_list import SmartProxyList, ProxyListTimedOut, ProxyListEmpty

logger = logging.getLogger(__name__)


class Non200StatusCodeException(Exception):
    pass


class SoupLoader:
    headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"}

    bot_headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}

    def __init__(self, bot=False, use_proxies=True, timeout=25, proxy_retry_limit=10):
        self.session = requests.Session()
        self.proxies_list = SmartProxyList(requests_format=True)
        self.proxy = self.proxies_list.pop()
        # self.tested_proxies = {}
        self.retry_limit = proxy_retry_limit
        self.error_count = 0
        self.use_proxies = use_proxies
        self.timeout = timeout
        self._proxies_tried = 0
        self.bot = bot
        self.headers = SoupLoader.bot_headers if bot else SoupLoader.headers

    def __call__(self, link, proxies_per_test=10):
        try:
            response = self.loadpage(link)
            if not response:
                raise Non200StatusCodeException
        except (requests.RequestException, Non200StatusCodeException, timeout):
            data = self.next_proxy(link, proxies_per_test)
            self.error_count = 0
            return data
        else:
            self.error_count = 0
            return self.process_response(response)

    def next_proxy(self, url, proxies_per_test):
        try:
            self.proxy = self.proxies_list.pop_tested(url)
        except (ProxyListTimedOut, ProxyListEmpty):
            response, proxies = self.test_proxies(url, proxies_per_test,
                                                  self.timeout)
            self.proxies_list.update(url, proxies)
            return self.process_response(response)
        else:
            return self(url, proxies_per_test)

    def test_proxies(self, url, proxies_per_test, timeout, max_workers=10):
        proxies = [self.proxies_list.pop() for _ in range(proxies_per_test)]

        session = FuturesSession(max_workers=max_workers)
        futures = [(session.get(url,
                                headers=self.headers,
                                proxies=proxy,
                                timeout=timeout), proxy) for proxy in proxies]
        good_proxies = []
        response = None
        for future, proxy in futures:
            try:
                r = future.result()
            except Exception:
                pass
            else:
                if r:
                    response = r
                    good_proxies.append(proxy)
        return response, good_proxies

    @staticmethod
    def process_response(response):
        return BeautifulSoup(response.text, 'lxml')

    def loadpage(self, link):
        logger.warning('test')
        if self.use_proxies:
            res = self.session.get(link, headers=self.headers,
                                   proxies=self.proxy,
                                   timeout=self.timeout)
        else:
            res = self.session.get(link, headers=self.headers)
        return res


class LxmlSoupLoader(SoupLoader):
    def __call__(self, link, proxies_per_test=10):
        req = self.loadpage(link)

        if req:
            return fromstring(req.text)
        elif not self.use_proxies:
            self.use_proxies = True
        else:
            self.proxies = self.proxies_list.pop()

        return self(link)
