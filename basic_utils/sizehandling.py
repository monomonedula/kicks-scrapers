import os
import csv
import logging
import re

from .decorators import size_value_format_check

logger = logging.getLogger(__name__)

csv_file_names = [('adidas.csv', 'adidas'), ('converse.csv', 'converse'),  ('nike.csv', 'nike'),
                  ('puma.csv', 'puma', 'oneill'),
                  ('skechers.csv', 'skechers'), ('vans.csv', 'vans')]

size_system_order = ('usm', 'usw', 'uk', 'eu', 'cm')


def _load_tables():
    this_dir, _ = os.path.split(__file__)
    path = os.path.join(this_dir, 'size_tables')
    s_tables = {}

    for name, *brands in csv_file_names:
        with open(os.path.join(path, name)) as file:
            reader = csv.DictReader(file, fieldnames=size_system_order)
            ls = [row for row in reader]
            for brand in brands:
                s_tables[brand] = ls

    return s_tables


size_tables = _load_tables()


def size_to_db_format(size_system, value, brand=None, default_brand='adidas'):
    global size_tables
    value = format_size_number(value)

    if not brand or brand not in size_tables:
        logger.debug('Given brand "{}". Using default brand "{}" instead.'.format(brand, default_brand))
        brand = default_brand
    brand_table = size_tables[brand]
    for row in brand_table:
        if row[size_system] == value:
            return [ss + row[ss] for ss in size_system_order if row[ss]]

    logger.warning('Given size "{}", size system "{}", brand "{}". \
 Unable to convert it into other size systems.'.format(value, size_system, brand))
    return []


@size_value_format_check
def format_size_number(s):
    s = s.replace(",", ".")
    s = s.replace(" ", "")
    s = s.replace("1/3", ".3")
    s = s.replace("2/3", ".7")
    s = s.replace("1/2", ".5")
    s = re.sub("[^0-9./½⅓⅔]", "", s)
    s = s.replace("½", ".5")
    s = s.replace("⅓", ".3")
    s = s.replace("⅔", ".7")
    s = s.replace(".0", "")
    return s


if __name__ == '__main__':
    size = size_to_db_format(value="10", brand='adidas', size_system='usm')
    print(s)