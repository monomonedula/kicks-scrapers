import logging
import re
from datetime import datetime, timedelta
import json

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
        if not self.proxies_list or self.expired():
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
    # link = "https://free-proxy-list.net"
    link = "http://www.gatherproxy.com/"
    res = requests.get(link)
    return BeautifulSoup(res.text, 'lxml')


def get_proxies_list(*, requests_format=False):
    """ anonymity = 'elite proxy' by default
        may be also: 'anonymous', 'transparent'

        returns list of (adress, port) tuples
    """
    bs = load_free_proxies_soup()
    table = bs.find('table')
    scripts = table.find_all('script')
    res = []
    for s in scripts:
        try:
            data = re.search(r"({[^}]*})", s.text)[0]
            data = json.loads(data)
        except Exception as e:
            print(e)
        else:
            if data['PROXY_TYPE'] not in ('Elite', 'Anonymous'):
                continue
            adress = data['PROXY_IP']
            port = data['PROXY_PORT']
            port = int(port, 16)
            if requests_format:
                res.append({'https': f'http://{adress}:{port}',
                            'http': f'http://{adress}:{port}'})
            else:
                res.append((adress, str(port)))

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
