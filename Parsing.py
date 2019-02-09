from time import sleep
import logging
import gc

from dbhandling import parserdb

logger = logging.getLogger(__name__)


class TooManyErrors(Exception):
    pass


class BaseParser:
    def __init__(self, *, get_offers_list, get_item_dict,
                 driver_wrapper=None, soup_loader=None,
                 min_sleep_time=2.0):
        self.sleep_time = min_sleep_time
        self.get_offers_list = get_offers_list
        self.get_item_dict = get_item_dict
        self.driver_wrapper = driver_wrapper
        self.soup_loader = soup_loader or driver_wrapper.load_soup
        if not self.driver_wrapper and not self.soup_loader:
            raise ValueError('Neither driver_wrapper nor soup_loader are given')
        self.exceptions_counter = 0
        self.items_gathered = 0

    def __call__(self, links, maxpage=None):
        for i, data in enumerate(links):
            link = data.pop('link')
            if maxpage and i > maxpage:
                logger.info('Reached max page limit.')
                break
            sleep(self.sleep_time)
            logger.info('Loading %s' % link)
            bs_obj = self.soup_loader(link)
            logger.info('Parsing page {} ...'.format(link))
            for item in self._parse_page(bs_obj, page_data=data):
                yield item
            gc.collect()

    def _parse_page(self, bs_obj, page_data):
        for offer in self.get_offers_list(bs_obj):
            self.items_gathered += 1
            try:
                request = {'offer': offer, **page_data}
                item = self.get_item_dict(request=request)
            except Exception:
                logger.exception(page_data)
                self.exceptions_counter += 1
                if self.too_many_errors():
                    raise TooManyErrors("items total: %s , exceptions: %s" % (self.items_gathered,
                                                                              self.exceptions_counter))
            else:
                if item:
                    yield item

    def too_many_errors(self):
        return self.exceptions_counter / self.items_gathered > 0.5 and self.items_gathered > 100


def database_writer(item_generator, scraper_name, item_id_field='link', buffer_size=200):
    try:
        buffer = {}
        logger.info('Creating session record...')
        session_id = parserdb.new_scrape_session(scraper_name)
        logger.info('Created session_id: %s' % session_id)
        total = 0
        for num, item in enumerate(item_generator, start=1):
            if item is not None:
                total += 1
                buffer[item[item_id_field]] = item
            if len(buffer) == buffer_size:
                logger.info('Writing batch to elasticsearch. Batch size: %s, session id: %s' % (buffer_size, session_id))
                parserdb.scrape_session_still_open(session_id, total)
                parserdb.write_docs_batch_to_index(batch=list(buffer.values()),
                                                   id_field=item_id_field)
                buffer = {}
        if buffer:
            logger.info('Writing last batch to elasticsearch. session id: %s' % session_id)
            parserdb.write_docs_batch_to_index(batch=list(buffer.values()),
                                               id_field=item_id_field)
    except (Exception, KeyboardInterrupt):
        logger.critical({'message': 'Error occured.'})
        parserdb.critical_session_exit(session_id)
        raise
    logger.info('Closing scraping session %s. Total items obtained: %s' % (session_id, total))
    parserdb.scrape_session_mark_closed(session_id)


def merge_size_fields(item1, item2):
    sizes = set(item1['sizes'])
    sizes.update(item2['sizes'])
    item1['sizes'] = list(sizes)
    return item1


def database_size_layer_writer(item_generator, scraper_name, max_buffer_size=200,
                               item_id_field='link', merge=merge_size_fields,):
    try:
        logger.info('Creating new tmp scraping session...')
        tmp_session_index, session_id = parserdb.new_tmp_scrape_session(scraper_name)
        logger.info('Created new tmp scraping session %s, index_name %s' % (session_id, tmp_session_index))
        total = 0
        buffer = {}
        for num, item in enumerate(item_generator, start=1):
            if item is not None:
                total += 1
                item['sl'] = True
                item_id = item[item_id_field]
                if item_id in buffer:
                    buffer[item_id] = merge(buffer[item_id], item)
                else:
                    buffer[item_id] = item
            if len(buffer) == max_buffer_size:
                parserdb.scrape_session_still_open(session_id, total)
                logger.info(
                    'Writing batch to elasticsearch. Batch size: %s, session id: %s' % (max_buffer_size, session_id))
                parserdb.write_tmp(items=list(buffer.values()), index=tmp_session_index)
                buffer = {}
        if buffer:
            logger.info('Writing batch to elasticsearch. Batch size: %s, session id: %s' % (len(buffer), session_id))
            parserdb.write_tmp(items=list(buffer.values()), index=tmp_session_index)

        logger.info('Commiting tmp session from tmp index %s' % tmp_session_index)
        parserdb.commit(tmp_session_index)
        logger.info('Dropping index %s' % tmp_session_index)
        parserdb.drop_index(tmp_session_index)
        logger.info('Closing scraping session %s. Total items obtained: %s' % (session_id, total))
        parserdb.scrape_session_mark_closed(session_id)
    except (Exception, KeyboardInterrupt):
        logger.critical({'message': 'Error occured. Dropping index %s' % tmp_session_index})
        parserdb.drop_index(tmp_session_index)
        parserdb.critical_session_exit(session_id)
        raise


def sl_link_gen(*, baselinks, sizes_list, get_pg_lim, ipp=None):
    for l in baselinks:
        for s in sizes_list:
            pg_lim = get_pg_lim(link=l, size=s)
            for p in range(pg_lim):
                if ipp:
                    yield {'link': l.format(position=ipp*p, size=s, ipp=ipp), 'size': s}
                else:
                    yield {'link': l.format(position=p, size=s), 'size': s}


def links(baselinks, maxpage, page_lim=None, ipp=None, start_from=1):
    for link in baselinks:
        mxpg = maxpage(link=link)
        for j in range(start_from, mxpg + 1):
            if page_lim and j > page_lim:
                return
            if ipp:
                yield {'link': link.format(position=j*ipp)}
            else:
                yield {'link': link.format(position=j)}
