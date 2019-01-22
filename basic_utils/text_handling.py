import logging
import os
import re


logger = logging.getLogger(__name__)

this_dir, _ = os.path.split(__file__)
colors_path = os.path.join(this_dir, 'colors.txt')

with open(colors_path) as file:
    colors = [c.replace('\n', '') for c in file.readlines()]


brands_list = ("Adidas", "Asics", "Nike", "Reebok", "Puma", "Vans", "Converse",
               "Skechers", "Columbia", "Umbro", "Timberland", "Under Armour",
               "Saucony" "Circa", "Dr. Martens", "Emerica", "etnies", "Fila",
               "O'Neill", "New Balance", "Fred Perry", "Ugg", "The North Face",
               "Osiris", "Ralph Lauren", "Diadora", "Geox", "Lakai", "DC",
               "Sperry", "Supra", "Volcom", "Lacoste", "Native", "KangaROOS", "Jordan",
               "Arkk Copenhagen", "SUPERGA", "Undefeated", "HUF", "NOVESTA", "TEVA",)


def only_digits(text):
    return re.sub("[^0-9]", "", text)


def contains_color(text):
    def stage1(s):
        res = 0
        for c in colors:
            res += s.count(c)
        return 0.5 * res

    def stage2(s):
        res = 0
        for c in colors:
            for word in s.split():
                res += c.count(word)
        return 0.25 * res

    text = text.lower()
    text = ' '.join(text.split())
    return stage1(text) + stage2(text)
