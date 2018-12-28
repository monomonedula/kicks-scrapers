import logging

import requests
from bs4 import BeautifulSoup
from selenium.webdriver import Firefox
from selenium.webdriver import FirefoxProfile
from selenium.common.exceptions import TimeoutException

from kicksbot.Parsing.webutils.get_proxies import ProxiesList

logger = logging.getLogger(__name__)


class Blocked(Exception):
    pass


class FirefoxWebdriverWrapper:
    def __init__(self, *, timeout=30, page_load_timeout=30, use_proxy=True,
                 load_images=True, cache=True, check_response=None, max_pages=100):
        self.proxies_list = ProxiesList()
        self.timeout = timeout
        self.use_proxy = use_proxy
        self.cache = cache
        self.load_images = load_images
        self.browser = Firefox(firefox_profile=self._get_profile(use_proxy), timeout=self.timeout)
        self.browser.set_page_load_timeout(page_load_timeout)
        self.page_load_timeout = page_load_timeout
        self.session = requests.Session()
        self.check_response = check_response

        self.max_pages = max_pages
        self.pages_count = 0

    def get(self, url):
        while True:
            try:
                if self.pages_count == self.max_pages:
                    self.reset_browser(new_proxy=False)

                self.browser.get(url)
                if self.check_response:
                    self.check_response(self.browser)
            except TimeoutException as e:
                if not self.use_proxy:
                    raise e
                logger.info('Timeout webdriver exception. Restarting with new proxy...')
            except Blocked as e:
                if not self.use_proxy:
                    raise e
                logger.warning("Blocked by website's security system. Restarting with new proxy...")
            else:
                self.pages_count += 1
                return

            self.reset_browser(new_proxy=True)

    def _get_profile(self, new_proxy=True):
        if new_proxy and not self.use_proxy:
            raise ValueError('_get_profile method cannot be called with new_proxy=False argument if the object is \
            configured not to use proxies (use_proxies should be equal True)')

        if self.use_proxy and new_proxy:
            self.proxy_host, self.proxy_port = self.proxies_list.pop()

        fp = FirefoxProfile()
        if self.use_proxy:
            fp.set_preference("network.proxy.type", 1)
            fp.set_preference("network.proxy.http", self.proxy_host)  # HTTP PROXY
            fp.set_preference("network.proxy.http_port", int(self.proxy_port))
            fp.set_preference("network.proxy.ssl", self.proxy_host)  # SSL  PROXY
            fp.set_preference("network.proxy.ssl_port", int(self.proxy_port))
            fp.set_preference('network.proxy.socks', self.proxy_host)  # SOCKS PROXY
            fp.set_preference('network.proxy.socks_port', int(self.proxy_port))

        if not self.cache:
            fp.set_preference("browser.cache.disk.enable", False)
            fp.set_preference("browser.cache.memory.enable", False)
            fp.set_preference("browser.cache.offline.enable", False)
            fp.set_preference("network.http.use-cache", False)

        if not self.load_images:
            fp.set_preference("permissions.default.image", 2)

        fp.update_preferences()
        return fp

    def reset_browser(self, new_proxy):
        if new_proxy and not self.use_proxy:
            raise ValueError('reset_browser method cannot be called with new_proxy=False argument if the object is \
            configured not to use proxies (use_proxies should be equal True)')

        self.browser.quit()
        self.browser = Firefox(firefox_profile=self._get_profile(new_proxy=new_proxy),
                               timeout=self.timeout)
        self.browser.set_page_load_timeout(self.page_load_timeout)
        self.pages_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug('Closing browser...')
        self.browser.quit()

    def __del__(self):
        logger.debug('Closing browser...')
        self.browser.quit()

    def load_soup(self, url):
        self.get(url)
        return BeautifulSoup(self.browser.page_source, 'lxml')
