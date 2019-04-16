from datetime import datetime

import requests


url = 'https://v3.exchangerate-api.com/bulk/618b4fe9a4334137b4b17a5f/USD'


currency_rates_to_usd = requests.get(url).json()
_last_update = datetime.utcnow()


def get_currency_rates():
    global currency_rates_to_usd, _last_update
    if (datetime.utcnow() - _last_update).days > 0:
        currency_rates_to_usd = requests.get(url).json()
        _last_update = datetime.utcnow()
    return currency_rates_to_usd


def convert(frm, to, amount, ndigits=0):
    curr_rates = get_currency_rates()['rates']
    psbl_currs = set(curr_rates.keys())
    psbl_currs.add('USD')

    if frm not in psbl_currs or to not in psbl_currs:
        raise ValueError("Unsupported currency error.")

    if frm == 'USD':
        res = amount*curr_rates[to]
    elif to == 'USD':
        res = amount*(1/curr_rates[frm])
    else:
        res = amount*(curr_rates[to]/curr_rates[frm])

    res = round(res, ndigits)

    return int(res)
