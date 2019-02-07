import logging
from socket import timeout

from bs4 import BeautifulSoup
from lxml.html.soupparser import fromstring
import requests

from webutils.get_proxies import ProxiesList


logger = logging.getLogger(__name__)


class SoupLoader:
    headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:62.0) Gecko/20100101 Firefox/62.0"}

    bot_headers = {'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}

    def __init__(self, bot=False, use_proxies=True):
        self.session = requests.Session()
        self.proxies_list = ProxiesList(requests_format=True)
        self.proxies = self.proxies_list.pop()
        self.use_proxies = use_proxies
        self._proxies_tried = 0
        self.bot = bot
        self.headers = SoupLoader.bot_headers if bot else SoupLoader.headers

    def __call__(self, link):
        req = self.loadpage(link)

        if req:
            return BeautifulSoup(req.text, 'lxml')
        elif not self.use_proxies:
            self.use_proxies = True
        else:
            self.proxies = self.proxies_list.pop()

        return self(link)

    def loadpage(self, link):
        error_counter = 0
        logger.warning('test')
        if self.use_proxies:
            while True:
                try:
                    logger.info('new proxy: %s' % self.proxies)
                    res = self.session.get(link, headers=self.headers,
                                           proxies=self.proxies,
                                           timeout=20)
                except requests.exceptions.ProxyError:
                    logger.warning('Broken proxy {}. Popping another one...'.format(self.proxies))
                except requests.exceptions.Timeout:
                    logger.warning('Proxy connection timeout. Popping another one...')
                except requests.exceptions.SSLError:
                    logger.warning('SSLError. Popping another proxy ...')
                except requests.exceptions.ConnectionError:
                    if error_counter > 2:
                        logger.warning('Connection error. Popping another proxy...')
                    else:
                        logger.warning('Connection error. Retrying. Retry count: {}'.format(error_counter))
                        error_counter += 1
                        continue
                except timeout:
                    logger.warning('Socket timeout. Trying another proxy ...')
                else:
                    logger.debug('Returning result')
                    return res

                logger.info('Trying new proxy...')
                self.proxies = self.proxies_list.pop()
        else:
            logger.info('Trying session')
            return self.session.get(link, headers=self.headers)


class LxmlSoupLoader(SoupLoader):
    def __call__(self, link):
        req = self.loadpage(link)

        if req:
            return fromstring(req.text)
        elif not self.use_proxies:
            self.use_proxies = True
        else:
            self.proxies = self.proxies_list.pop()

        return self(link)