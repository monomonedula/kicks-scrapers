from dbhandling.elastic_models import SneakerItem


class SLSneakerItemDiskBuff(SneakerItem):
    def get_bulk_tmp_update_dict(self):
        d = self.to_dict(include_meta=True)
        d['_op_type'] = 'update'
        d['script'] = self.get_tmp_update_script()
        d['upsert'] = self.get_upsert_dict()
        return d

    def get_tmp_update_script(self):
        return {
           'source': "ctx._source.sizes.addAll(params.sizes); ctx._source.price = params.price",
           'lang': 'painless',
           'params': {
               'price': self.price,
               'sizes': list(self.sizes),
           }
        }