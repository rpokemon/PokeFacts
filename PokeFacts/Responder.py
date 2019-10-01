#!/usr/bin/env python3

# Responder.py
# ~~~~~~~~~~~~
# This file is tasked with compiling a response given a list
# of call items (i.e. a list of results of DataPulls.get_info)


def xstr(x):
    if x is None:
        return ''
    return str(x)


def xget(source, prop):
    if type(source) == dict:
        if prop in source:
            return xstr(source[prop])
    elif type(source) == list:
        if prop < len(source) and prop >= 0:
            return xstr(source[prop])
    return ''


def xlist(L):
    if L is None:
        return []
    if not isinstance(L, list):
        L = [L]
    return [xstr(x) for x in L if x is not None]

# respondPokemon - function returns the response body
# of pokemon type objects (as returned by DataPulls.get_info)


def respond_pokemon(call_item):
    response = ''

    basename = xget(call_item, 'basename')
    en_name = xget(call_item['name'], 'english')
    jp_name = xget(call_item['name'], 'kana')
    rj_name = xget(call_item['name'], 'japanese')
    fdex_no = xget(call_item, 'dex_no').zfill(3)

    dex_entry = ' '.join(xlist(call_item['dex_entry']))
    pokeclass = xget(call_item, 'classification')
    types = xlist(call_item['types'])
    abilities = xlist(call_item['abilities'][:2])
    hidden_ability = xget(call_item["abilities"], 2)
    base_stats = xlist(call_item['base_stats'])
    evolutions = xlist(call_item['evolutions'])

    response += '**#' + fdex_no + ' ' + en_name + '** '
    response += '(Japanese ' + jp_name + ' ' + rj_name + ')'
    response += "\n\n"

    response += pokeclass + ' | Types: ' + (', '.join(types))
    if any(evolutions):
        response += ' | Evolutions: ' + (' '.join(evolutions))
    response += "\n\n"

    response += '_'+dex_entry+'_'
    response += "\n\n"

    response += '/'.join(base_stats)
    if any(abilities):
        response += ' | Abilities: '
        response += ' / '.join(abilities)
        if hidden_ability is not None and len(hidden_ability) > 0:
            response += ' / HA: ' + hidden_ability
    response += "\n\n"

    response += '[Bulbapedia](http://bulbapedia.bulbagarden.net/wiki/' + \
        basename+') | '
    response += '[Serebii](http://www.serebii.net/pokedex-sm/' + \
        fdex_no+'.shtml) | '
    response += '[Smogon](http://www.smogon.com/dex/sm/pokemon/' + \
        basename+'/) | '
    response += '[Pokemon.com](http://www.pokemon.com/us/pokedex/'+basename+')'
    response += "\n\n"

    return response

# respondPokemon - function returns the response body
# of ability type objects (as returned by DataPulls.get_info)


def respond_ability(call_item):
    response = ''

    name = xget(call_item, "name")
    basename = xget(call_item, "term").replace(' ', '')
    generation = xget(call_item, "introduced")
    description = xget(call_item, "description")

    response += '**' + name + '** '
    response += '(Introduced: gen ' + generation + ')'
    response += "\n\n"

    response += description
    response += "\n\n"

    response += '[Bulbapedia](http://bulbapedia.bulbagarden.net/wiki/'+name+') | '
    response += '[Serebii](https://www.serebii.net/abilitydex/' + \
        basename+'.shtml) | '
    response += '[Smogon](http://www.smogon.com/dex/sm/abilities/'+name+'/)'
    response += "\n\n"

    return response

# respondPokemon - function returns the response body
# of move type objects (as returned by DataPulls.get_info)


def respond_move(call_item):
    response = ''

    name = xget(call_item, "name")
    basename = xget(call_item, "term").replace(' ', '')
    move_type = xget(call_item, "typing")
    pp = xget(call_item, "pp")
    category = xget(call_item, "category")
    power = "varies" if category == "varies" else (
        xget(call_item, "power") or "-")
    accuracy = xget(call_item, "accuracy") or "-"
    description = xget(call_item, "description")

    response += '**' + name + '** '
    response += '(Category: ' + category + ')'
    response += "\n\n"

    response += move_type + ' | PP: ' + pp + \
        ' | Power: ' + power + " | Accuracy: " + accuracy
    response += "\n\n"

    response += description
    response += "\n\n"

    response += '[Bulbapedia](http://bulbapedia.bulbagarden.net/wiki/'+name+') | '
    response += '[Serebii](https://www.serebii.net/attackdex-sm/' + \
        basename+'.shtml) | '
    response += '[Smogon](http://www.smogon.com/dex/sm/abilities/'+name+'/)'
    response += "\n\n"

    return response

# respondPokemon - function returns the response body
# of item type objects (as returned by DataPulls.get_info)


def respond_item(call_item):
    response = ''

    name = xget(call_item, "name")
    basename = xget(call_item, "term").replace(' ', '')
    description = xget(call_item, "description")

    response += '**' + name + '** '
    response += "\n\n"

    response += description
    response += "\n\n"

    response += '[Bulbapedia](http://bulbapedia.bulbagarden.net/wiki/'+name+') | '
    response += '[Serebii](https://www.serebii.net/attackdex-sm/' + \
        basename+'.shtml) | '
    response += '[Smogon](http://www.smogon.com/dex/sm/items/'+name+'/)'
    response += "\n\n"

    return response

# getResponse - this function should return the response body
# for the given call item (as returned by DataPulls.get_info)


def get_response(item, is_last=False):
    response_types = {
        "pokemon":  respond_pokemon,
        "ability":  respond_ability,
        "move":     respond_move,
        "item":     respond_item,
    }
    try:
        response = response_types[item.type](item.get())
    except KeyError:
        response = ""

    if not is_last:
        response += '---'
        response += "\n\n"

    return response
