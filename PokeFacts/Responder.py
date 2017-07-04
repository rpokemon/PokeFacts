#!/usr/bin/env python3

# Responder.py
# ~~~~~~~~~~~~
# This file is tasked with compiling a response given a list
# of call items (i.e. a list of results of DataPulls.getInfo)

def xstr(x):
    if x is None:
        return ''
    return str(x)

# getResponse - this function should return the response body
# for the given call item (as returned by DataPulls.getInfo)
def getResponse(call_item, is_last = False):
    response = ''

    basename = xstr(call_item['basename'])
    en_name  = xstr(call_item['name']['english'])
    jp_name  = xstr(call_item['name']['kana'])
    rj_name  = xstr(call_item['name']['japanese'])
    fdex_no  = xstr(call_item['dex_no']).zfill(3)

    response += '**#' + fdex_no + ' ' + en_name + '** '
    response += '(Japanese ' + jp_name + ' ' + rj_name + ')'
    response += "\n\n"

    response += xstr(call_item['classification']) + ' | ' + xstr(' '.join(call_item['types']))
    response += "\n\n"

    if any(call_item['evolutions']):
        response += 'Evolutions: ' + xstr(' '.join(call_item['evolutions']))
        response += "\n\n"

    response += '[Bulbapedia](http://bulbapedia.bulbagarden.net/wiki/'+basename+') |'
    response += '[Serebii](http://www.serebii.net/pokedex-sm/'+fdex_no+'.shtml) |'
    response += '[Smogon](http://www.smogon.com/dex/sm/pokemon/'+basename+'/) |'
    response += '[Pokemon.com](http://www.pokemon.com/us/pokedex/'+basename+')'
    response += "\n\n"

    if not is_last:
        response += '---'
        response += "\n\n"

    return response