from datetime import datetime, timedelta, timezone
import logging

from fluent import asynchandler, handler
from elasticsearch import Elasticsearch


expire_days = 2


def main():
    log_format = {
        'where': '%(module)s.%(funcName)s',
        'type': '%(levelname)s',
        'stack_trace': '%(exc_text)s',
    }

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('')
    logger.setLevel(level=logging.INFO)
    h = asynchandler.FluentHandler('kicks.garbage_removal', host='localhost', port=24224)
    h.setLevel(level=logging.INFO)
    formatter = handler.FluentRecordFormatter(log_format)
    h.setFormatter(formatter)
    logging.getLogger('').addHandler(h)

    es = Elasticsearch(['http://localhost:9200/'])
    exp_time = (datetime.utcnow() - timedelta(days=expire_days))
    exp_time_int = exp_time.replace(tzinfo=timezone.utc).timestamp()
    resp = es.delete_by_query(index='kicks', q={'range': {'last_update': exp_time_int}})
    logging.info({'message': 'old documents deletion finished', 'documents_deleted': resp['deleted']})


if __name__ == "__main__":
    main()

