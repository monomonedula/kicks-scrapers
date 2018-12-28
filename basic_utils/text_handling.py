import logging
import os
import re


from fuzzywuzzy import fuzz, process


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


def identify_brand(name):
    def form(word):
        word = word.lower()
        return re.sub(r"\W", "", word)

    def b(word):
        return r"\b" + word + r"\b"

    def simple_identification(fname):
        for br in brands_list:
            if form(br) in fname:

                if len(br) < 4 and not re.search(b(br), name, re.IGNORECASE):
                    continue
                elif br == "Jordan":
                    logger.debug('Input name: "{}". Word Jordan found. Returning "Nike" instead ...'.format(name))
                    return "Nike"
                else:
                    logger.debug('Input name: "{}". Returning "{}"'.format(name, br))
                    return br

    brand = simple_identification(form(name))
    if brand:
        return brand

    fuzzy_brand = identify_brand_fuzzy(name)
    if fuzzy_brand:
        logger.warning('Input name: "{}". Fuzzy brand identification: {}'.format(name, fuzzy_brand))
        return fuzzy_brand[0]
    else:
        logger.warning('Unable to identify brand in string: "{}"'.format(name))


def identify_brand_fuzzy(name):
    return process.extractOne(name, brands_list, scorer=fuzz.partial_token_set_ratio, score_cutoff=91)


def get_brand_substring(name, brand=None):
    name_substrings = name.split()
    name_substrings = name_substrings[:3]
    name_substrings.extend([' '.join(name_substrings[:2]), ' '.join(name_substrings[:3])])
    if brand:
        res = process.extractOne(brand, name_substrings, scorer=fuzz.ratio)
    else:
        res = max((process.extractOne(s, brands_list, scorer=fuzz.ratio) for s in name_substrings), key=lambda x: x[1])

    return res[0] if res[1] > 90 else None
