import mongoengine

from dbhandling.scr_session import ScrapingSession


class SLDiskBufferScrapingSession(ScrapingSession):
    tmp_index_name = mongoengine.StringField(max_length=120)

    def __init__(self, *args, **values):
        super().__init__(*args, **values)
        self.tmp_index_name = self.generate_tmp_index_name(self.session_id)

    @classmethod
    def generate_tmp_index_name(cls, ss_uuid):
        return 'tmp-' + ss_uuid
