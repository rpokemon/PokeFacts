#!/usr/bin/env python3

# Responder.py
# ~~~~~~~~~~~~
# This file is tasked with compiling a response given a list
# of call items (i.e. a list of results of DataPulls.getInfo)

def xstr(x):
    if x is None:
        return ''
    return str(x)

# respondPokemon - function returns the response body
# of pokemon type objects (as returned by DataPulls.getInfo)
def respondPokemon(call_item)
    response = ''

    basename = xstr(call_item['basename'])
    en_name = xstr(call_item['name']['english'])
    jp_name = xstr(call_item['name']['kana'])
    rj_name = xstr(call_item['name']['japanese'])
    fdex_no = xstr(call_item['dex_no']).zfill(3)
    types = call_item['types']
    abilities = call_item['abilities'][:2]
    hidden_ability = call_item["abilities"][2]
    base_stats = call_item['base_stats']

    response += '**#' + fdex_no + ' ' + en_name + '** '
    response += '(Japanese ' + jp_name + ' ' + rj_name + ')'
    response += "\n\n"

    response += xstr(call_item['classification']) + ' | ' + xstr(' '.join(types)) 
    response += "\n\n"

    response += ' / '.join(abilities)
    response += (' / HA: ' + hidden_ability) if hidden_ability is not None else ''
    response += "\n\n"

    response += xstr('/'.join(base_stats))
    response += "\n\n"

    if any(call_item['evolutions']):
        response += 'Evolutions: ' + xstr(' '.join(call_item['evolutions']))
        response += "\n\n"

    response += '[Bulbapedia](http://bulbapedia.bulbagarden.net/wiki/'+basename+') |'
    response += '[Serebii](http://www.serebii.net/pokedex-sm/'+fdex_no+'.shtml) |'
    response += '[Smogon](http://www.smogon.com/dex/sm/pokemon/'+basename+'/) |'
    response += '[Pokemon.com](http://www.pokemon.com/us/pokedex/'+basename+')'
    response += "\n\n"

    return response

# respondPokemon - function returns the response body
# of ability type objects (as returned by DataPulls.getInfo)
def respondAbility(call_item)
    response = ''

    name = call_item["name"]
    basename = call_item.lower().replace(' ', '')
    generation = call_item["introduced"]
    description = call_item["description"]

    response += '**' + name + '** '
    response += '(Introduced: gen ' + generation + ')'
    response += "\n\n"

    response += xstr(description)
    response += "\n\n"

    response += '[Bulbapedia](http://bulbapedia.bulbagarden.net/wiki/'+name+') |'
    response += '[Serebii](https://www.serebii.net/abilitydex/'+basename+'.shtml) |'
    response += '[Smogon](http://www.smogon.com/dex/sm/abilities/'+name+'/)'
    response += "\n\n"

    return response

# respondPokemon - function returns the response body
# of move type objects (as returned by DataPulls.getInfo)
def respondMove(call_item)
    response = ''

    name = call_item["name"]
    basename = call_item.lower().replace(' ', '')
    move_type = call_item["typing"]
    pp = call_item["pp"]
    category = call_item["category"]
    power = "varies" if category == "varies" else (call_item["power"] or "-")
    accuracy = call_item["accuracy"] or "-"
    description = call_item["description"]

    response += '**' + name + '** '
    response += '(Category: ' + category + ')'
    response += "\n\n"

    response += move_type + ' | PP: ' + pp + '| Power: ' + power + " | Accuracy: " + accuracy
    response += "\n\n"

    response += description
    response += "\n\n"

    response += '[Bulbapedia](http://bulbapedia.bulbagarden.net/wiki/'+name+') |'
    response += '[Serebii](https://www.serebii.net/attackdex-sm/'+basename+'.shtml) |'
    response += '[Smogon](http://www.smogon.com/dex/sm/abilities/'+name+'/)'
    response += "\n\n"

    return response

# respondPokemon - function returns the response body
# of item type objects (as returned by DataPulls.getInfo)
def respondItem(call_item)
    response = ''

    name = call_item["name"]
    basename = call_item.lower().replace(' ', '')
    description = call_item["description"]

    response += '**' + name + '** '
    response += "\n\n"

    response += description
    response += "\n\n"

    response += '[Bulbapedia](http://bulbapedia.bulbagarden.net/wiki/'+name+') |'
    response += '[Serebii](https://www.serebii.net/attackdex-sm/'+basename+'.shtml) |'
    response += '[Smogon](http://www.smogon.com/dex/sm/items/'+name+'/)'
    response += "\n\n"

    return response

# getResponse - this function should return the response body
# for the given call item (as returned by DataPulls.getInfo)
def getResponse(call_item, is_last = False):  
    response_types = {
        "pokemon":  respondPokemon,
        "ability":  respondAbility,
        #"move":     respondMove,
        #"item":     respondItem,
    }
    try:
        response = response_types[call_item["type"]](call_item)
    except KeyError:
        response = ""

    if not is_last:
        response += '---'
        response += "\n\n"

    return response