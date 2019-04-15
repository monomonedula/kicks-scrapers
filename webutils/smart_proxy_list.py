import re
from datetime import timedelta, datetime

from webutils.get_proxies import ProxiesList


class SmartProxyList(ProxiesList):
    def __init__(self, requests_format=False,
                 expiration_timedelta=timedelta(minutes=15),
                 test_expiration_timedelta=None):
        super().__init__(requests_format=requests_format,
                         expiration_timedelta=expiration_timedelta)
        self.tested_proxies = {}
        self.test_exp_td = test_expiration_timedelta or self.exp_td

    def pop_tested(self, url):
        domain_name = self._domain(url)
        proxies, _ = self.tested_proxies.get(domain_name, (None, None))
        if not proxies:
            raise ProxyListEmpty
        if self.tested_expired(domain_name):
            raise ProxyListTimedOut
        return proxies.pop()

    def tested_expired(self, domain_name):
        _, last_update = self.tested_proxies[domain_name]
        td = datetime.utcnow() - last_update
        return td > self.test_exp_td

    @staticmethod
    def _domain(link):
        pattern = re.compile(r"https?://(www\.)?")
        return pattern.sub('', link).strip().strip('/')

    def update(self, url, tested_proxies):
        domain_name = self._domain(url)
        self.tested_proxies[domain_name] = (
            tested_proxies,
            datetime.utcnow(),
        )


class ProxyListEmpty(Exception):
    pass


class ProxyListTimedOut(Exception):
    pass
