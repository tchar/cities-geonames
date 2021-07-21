import os
import unicodedata
import re


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


def get_aliases(*names):
    remove_specials = re.escape('~`!@#$%^&*()_-+=[{]}\\|:;"\'<,>.?/')
    remove_specials = '[{}]'.format(remove_specials)
    regexes = [
        remove_specials,
        r'[^a-zA-Z\s]',
        r'[^a-zA-Z]'
    ]

    names = list(names)
    stripped = map(strip_accents, names)
    stripped = list(stripped)
    names.extend(stripped)

    aliases_set = set()
    aliases = []
    for name in names:
        name = name.strip()
        for regex in regexes:
            name_alt = re.sub(regex, '', name)
            if not name_alt:
                continue
            name_alt_lower = name_alt.lower()
            if name_alt.strip() == '':
                continue
            if name_alt_lower not in aliases_set:
                aliases.append(name_alt)
                aliases_set.add(name_alt_lower)
    
    assert all(map(lambda x: x.strip() != '', aliases))
    return aliases


def get_countries(use_foreign_languages=False):
    alias_info = {}
    if use_foreign_languages:
        with open(os.path.join('data', 'countryinfo_alts.txt')) as f:
            for line in f:
                line = line.strip().split('\t')
                cid, aliases = line
                aliases = aliases.split(',')
                aliases = map(str.strip, aliases)
                aliases = filter(None, aliases)
                aliases = list(aliases)
                alias_info[cid] = aliases

    info = {}
    with open(os.path.join('data', 'countryinfo.txt')) as f:
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                continue
            line = line.strip().split('\t')
            line = map(str.strip, line)
            line = list(line)
            iso2, iso3, _, _, country_name = line[:5]
            cid = line[16]

            country_names_alt = get_aliases(country_name, *alias_info.get(cid, []))
            assert all(country_names_alt)

            info[iso2.upper()] = {
                'id': int(cid),
                'iso2': iso2.upper(),
                'iso3': iso3.upper(),
                'name': country_name,
                'aliases': country_names_alt
            }
    return info


def get_cities(use_foreign_languages=False):
    countries_info = get_countries(use_foreign_languages=use_foreign_languages)
    with open(os.path.join('data', 'cities15000.txt')) as f:
        for line in f:
            line = line.split('\t')

            _id, city_name, city_name_ascii, city_names_foreign = map(
                str.strip, line[:4])
            cc = line[8].strip()
            cc2 = line[9].strip()
            state = line[10].strip()
            population = int(line[14].strip())
            timezone = line[17].strip()

            ccs = {cc: True}
            if cc2:
                cc2 = cc2.split(',')
                cc2 = map(str.strip, cc2)
                ccs.update({c: True for c in cc2})
            ccs = map(lambda c: countries_info[c], ccs)
            countries = list(ccs)

            if use_foreign_languages:
                city_names_foreign = city_names_foreign.split(',')
                city_names_foreign = map(str.strip, city_names_foreign)
            else:
                city_names_foreign = ()

            city_names_alt = get_aliases(
                city_name, city_name_ascii, *city_names_foreign)

            assert all(city_names_alt)

            city_names = {'name': city_name, 'aliases': city_names_alt}
            yield int(_id), city_names, countries, state, population, timezone
