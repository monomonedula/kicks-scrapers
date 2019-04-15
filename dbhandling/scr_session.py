import os
import uuid
from datetime import datetime
import logging

import mongoengine

logger = logging.getLogger(__name__)

mongoengine.connect(db='kicks')


class ScrapingSession(mongoengine.Document):
    pid = mongoengine.IntField(required=True, default=os.getpid)
    documents_count = mongoengine.IntField(default=0)
    scraper = mongoengine.StringField(required=True)
    open = mongoengine.BooleanField(default=True)
    session_id = mongoengine.UUIDField(required=True,
                                       binary=False, primary_key=True)
    last_activity = mongoengine.DateTimeField(default=datetime.utcnow)
    start_time = mongoengine.DateTimeField(default=datetime.utcnow)
    termination_time = mongoengine.DateTimeField()
    is_ok = mongoengine.BooleanField(default=True)

    @classmethod
    def open_new_session(cls, scraper_name, allow_concurrent_sessions=False):
        logger.info('Creating session record...')
        if not allow_concurrent_sessions and \
                cls.objects(scraper=scraper_name, open=True):
            raise ConcurrentSessionError('Cannot start new session for this scraper '
                                         'because scraper with the same name is already running.')
        session = cls.get_new_session(scraper_name)
        session.save()
        return session

    @classmethod
    def get_new_session(cls, scraper_name):
        ssid = uuid.uuid1()
        session = cls(session_id=ssid.hex,
                      scraper=scraper_name,)
        return session

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(exc_type, Exception):
            self.critical_exit()
        else:
            self.mark_as_closed()

    @classmethod
    def is_finished(cls, scraper_name):
        return not cls.objects(scraper=scraper_name, is_open=True)

    def mark_as_closed(self):
        logger.info({'message': 'Exiting scraping session.',
                     'session_id': self.id,
                     'docs_count': self.documents_count, })
        self.modify(set__open=False, set__termination_time=datetime.utcnow())

    def critical_exit(self):
        logger.critical({'message': 'Crititcal session exit.',
                         'session_id': self.id,
                         'docs_count': self.documents_count})
        self.modify(set__open=False, set__termination_time=datetime.utcnow(),
                    set__is_ok=False)

    def update_status(self, doc_count):
        self.modify(set__last_activity=datetime.utcnow(),
                    set__documents_count=doc_count)


class ConcurrentSessionError(Exception):
    pass
