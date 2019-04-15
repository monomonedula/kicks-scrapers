
import logging
import re

from .decorators import size_value_format_check

logger = logging.getLogger(__name__)


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
