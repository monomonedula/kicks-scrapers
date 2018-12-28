import logging

from googletrans import Translator as Trans


logger = logging.getLogger(__name__)


class CachedTranslator(Trans):
    def __init__(self, service_urls=None, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)', max_cache=50):
        self.cache = dict()
        self.free_space = max_cache
        super().__init__(service_urls=service_urls, user_agent=user_agent)

    def translate(self, text, dest='en', src='auto'):
        cached = self._find_in_cache(text, dest, src)
        if cached:
            return cached
        else:
            translation = super(CachedTranslator, self).translate(text, dest=dest, src=src)
            self._add_to_cache(translation, src)
            return translation

    def _find_in_cache(self, text, dest, src):
        logger.debug('Searching in cache for (text={}, dest={}, src={}) translation'.format(text, dest, src))
        records = self.cache.get(text)
        if records:
            for i, record in enumerate(records):
                trans, freq, src_auto = record
                if trans.dest == dest and (trans.src == src or (src == 'auto' and src_auto)):
                    self.cache[text][i][1] += 1
                    return trans

        logger.debug('Did not manage to find any occurance for (text={}, dest={}, src={}) word'.format(text, dest, src))
        return None

    def _add_to_cache(self, translation, src):
        logger.debug('Adding translation {}'.format(translation))
        self.free_space -= 1
        while self.free_space < 0:
            logger.debug('Need more cache space ...')
            self._del_one_record()

        record = [translation, 1, src == 'auto']
        if translation.origin in self.cache:
            self.cache[translation.origin].append(record)
        else:
            self.cache[translation.origin] = [record]

    def _del_one_record(self):
        logger.debug('Searching for the oldest and least used record to delete from cache...')
        least_used = None # record for deletion
        for origin in self.cache:
            for i, rec in enumerate(self.cache[origin]):
                if least_used is None or rec[1] < least_used[1]: # frequency lower than current lowest frequency
                    least_used = self.cache[origin][i]

        origin = least_used[0].origin
        self.cache[origin].remove(least_used)
        self.free_space += 1
        logger.debug('1 free cache position acquired')


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s',
                        level=logging.DEBUG)

    translator = CachedTranslator(max_cache=5)
    for word in ('czarny', 'ziemniaczki', 'zielonny', 'uczelnia', 'przyjaciołka'):
        print(translator.translate(word).text)

    print('here')
    print(translator.cache)
    translator.translate('uczelnia')
    print(translator.cache)
    translator.translate('biały')
    print(translator.cache)

