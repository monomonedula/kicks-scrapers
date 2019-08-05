import pytest

from .pipelines import KicksScraperPipeline, SessionedKicksScraperPipeline,\
    EmptyBufferWriteException, BufferOverflowException
from .spiders.runrepeat_tests import random_strings_gen


class ConnectionMock:
    pass


class BulkMock:
    def __init__(self):
        self._mock_written_items = []

    def __call__(self, conn, items):
        self._mock_written_items.extend(items)


class SpiderMock:
    def __init__(self, name):
        self.name = name


class ElasticItemMock:
    class _Meta:
        def __init__(self, id):
            self.id = id

    def __init__(self, id, data=None):
        self.meta = self._Meta(id)
        self._data = data

    def get_bulk_update_dict(self):
        return {'id': self.meta.id, 'data': self._data}


class ItemMock:
    def __init__(self, id, data):
        self._id = id
        self._data = data

    def to_elastic(self):
        return ElasticItemMock(self._id, self._data)


def get_filled_buffer(size, fill_size):
    buffer = KicksScraperPipeline.ItemsBuffer(size)
    for id_ in range(fill_size):
        buffer.add(ElasticItemMock(id_))
    return buffer


@pytest.mark.parametrize('size', [10, 1000, 200, 0, -20])
def test_items_buffer_size(size):
    buffer = get_filled_buffer(size, size)
    next_unique_id = size
    with pytest.raises(BufferOverflowException):
        buffer.add(ElasticItemMock(next_unique_id))


@pytest.mark.parametrize('size,fill',
                         [(10, 0),
                          (1000, 10),
                          (200, 200),
                          (0, 0),
                          (-20, 0)])
def test_items_buffer_is_full(size, fill):
    assert get_filled_buffer(size, fill).is_full() is (fill >= size)


@pytest.mark.parametrize('size,fill',
                         [(10, 0),
                          (1000, 10),
                          (200, 200),
                          (0, 0),
                          (-20, 0)])
def test_item_buffer_is_empty(size, fill):
    assert get_filled_buffer(size, fill).is_empty() is (fill == 0)


@pytest.mark.parametrize('size,fill',
                         [(10, 0),
                          (1000, 10),
                          (200, 200),
                          (0, 0),
                          (-20, 0)])
def test_item_buffer_length(size, fill):
    assert len(get_filled_buffer(size, fill)) == fill


@pytest.mark.parametrize('ids',
                         [(1, 2, 3, 4, 5),
                          (10, 100, 500),
                          (11, 11, 0, 0, 30, 44, 45, 30),
                          (0, 1, 1, 1),
                          ('some_id', 'another_id', 'another_id2', 'some_id')])
def test_item_buffer_ids(ids):
    buffer, _ = get_filled_buffer_with_ids(ids)
    assert len(buffer) == len(set(ids))


@pytest.mark.parametrize('ids',
                         [(1, 2, 3),
                          [],
                          ('123', '123', '55', '43_2', '43_2', '32_3'),
                          (1, 4, 4, 10, 5, 10, 3)])
def test_item_buffer_retrieve(ids):
    buffer, items = get_filled_buffer_with_ids(ids)
    assert buffer.retrieve() == list(
        {item.meta.id: item for item in items}.values()
    )


def test_item_buffer_retrieve_empty():
    buffer, items = get_filled_buffer_with_ids(
        list(random_strings_gen(30))
    )
    buffer.retrieve()
    assert buffer.is_empty() is True


def get_filled_buffer_with_ids(ids):
    items = [ElasticItemMock(i) for i in ids]
    buffer = KicksScraperPipeline.ItemsBuffer(len(ids))
    for item in items:
        buffer.add(item)
    return buffer, items


@pytest.mark.parametrize('items_number, buff_size',
                         [(100, 100), (101, 100), (400, 10),
                          (10, 200), (0, 300), (400, 1000),
                          (30, 100), (1, 10)])
def test_pipeline_process_item(items_number, buff_size):
    written_items = []

    def bulk_mock(connection, items):
        written_items.extend(items)

    pipeline, items = prepare_pipeline(items_number, buff_size, bulk_mock)
    dicts = get_update_dicts(items)
    n = buff_size * (items_number // buff_size)
    assert written_items == dicts[:n]


def prepare_pipeline(items_number, buff_size, bulk_mock):
    items = n_items(items_number)
    spider = SpiderMock('some_spider')
    pipeline = KicksScraperPipeline(ConnectionMock(), buff_size, bulk_mock)
    for item in items:
        pipeline.process_item(item, spider)
    return pipeline, items


def get_update_dicts(items):
    return [it.to_elastic().get_bulk_update_dict() for it in items]


def n_items(amount):
    return [ItemMock(i, f'some_data{i}') for i in range(amount)]
