import logging
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class ProxiesList:
    def __init__(self, requests_format=False, expiration_timedelta=timedelta(minutes=15)):
        self.use_requests_lib_format = requests_format
        self.proxies_list = get_proxies_list(requests_format=self.use_requests_lib_format)
        self.last_update = datetime.utcnow()
        self.exp_td = expiration_timedelta

    def pop(self):
        if not self.proxies_list:
            logger.info('Proxies list is empty. Calling refresh function...')
            self.refresh()
        if self.expired():
            logger.info('Proxies list update expired. Calling refresh function...')
            self.refresh()

        logger.debug('Popping proxy list element {} ...'.format(self.proxies_list[-1]))
        return self.proxies_list.pop()

    def expired(self):
        td = datetime.utcnow() - self.last_update
        if td > self.exp_td:
            logger.info('Proxies list update expired. Last update more than {} ago'.format(self.exp_td))
            return True
        return False

    def refresh(self):
        logger.info('Refreshing proxies list...')
        self.proxies_list = get_proxies_list(requests_format=self.use_requests_lib_format)
        self.last_update = datetime.utcnow()



def load_free_proxies_soup():
    link = "https://free-proxy-list.net"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/63.0.3239.84 Chrome/63.0.3239.84 Safari/537.36"}

    session = requests.Session()
    req = session.get(link, headers=headers)
    return BeautifulSoup(req.text, 'lxml')


def get_proxies_list(*, anonymity='elite proxy', requests_format=False):
    ''' anonymity = 'elite proxy' by default
        may be also: 'anonymous', 'transparent'

        returns list of (adress, port) tuples
    '''
    bs = load_free_proxies_soup()
    rows = bs.find_all('tr')
    res = []
    for row in rows:
        if row.find('td', text=anonymity):
            tds = row.find_all('td')
            adress = tds[0].text
            port = tds[1].text
            if requests_format:
                res.append({'https': ('http://' + adress + ':' + port),
                        'http': ('http://' + adress + ':' + port)})
            else:
                res.append((adress, port))

    logger.debug('Retrieved proxies: {}'.format(res))
    res.reverse()
    return res


def proxy_to_req_format(adress, port):
    return {
        'https': ('http://' + adress + ':' + port),
        'http': ('http://' + adress + ':' + port)
    }


if __name__ == '__main__':
    proxies = get_proxies_list(requests_format=True)
    print('Proxies:')
    for proxy in proxies:
        print(proxy)

    print(len(proxies))
