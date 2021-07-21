import os
import sqlite3
from process_cities import get_cities

def export_db(db, file_path):
    with open(file_path, 'w') as f:
        for line in db.iterdump():
            f.write(line + '\n')


def create_db(output_dir, full=False):
    basename = 'cities'
    if full:
        basename += '-full'

    db_filepath = os.path.join(output_dir, basename + '.sqlite3')
    sql_filepath = os.path.join(output_dir, basename + '.sql')
   
    if os.path.exists(sql_filepath):
        os.remove(sql_filepath)
    
    if os.path.exists(db_filepath):
        os.remove(db_filepath)

    db = sqlite3.connect(db_filepath)

    cur = db.cursor()
    cur.execute('PRAGMA foreign_keys = ON;')

    cur.execute('''CREATE TABLE IF NOT EXISTS meta (
                city_name_chunks_max INTEGER)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS countries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT COLLATE NOCASE,
                iso2 TEXT UNIQUE COLLATE NOCASE,
                iso3 TEXT UNIQUE COLLATE NOCASE)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS country_names_aliases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE COLLATE NOCASE)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS countries_aliases (
                country_id INTEGER,
                alias_id INTEGER,
                UNIQUE(country_id, alias_id),
                FOREIGN KEY(country_id) REFERENCES countries(id) ON DELETE CASCADE
                FOREIGN KEY(alias_id) REFERENCES country_names_aliases(id) ON DELETE CASCADE)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS states (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                country_id INTEGER,
                name TEXT COLLATE NOCASE,
                UNIQUE(country_id, name),
                FOREIGN KEY(country_id) REFERENCES countries(id) ON DELETE CASCADE)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS timezones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT COLLATE NOCASE UNIQUE)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY,
                timezone_id INTEGER,
                name TEXT COLLATE NOCASE,
                population INTEGER,
                FOREIGN KEY(timezone_id) REFERENCES timezones(id) ON DELETE CASCADE)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS cities_countries(
                city_id INTEGER,
                country_id INTEGER,
                UNIQUE(city_id, country_id)
                FOREIGN KEY(city_id) REFERENCES cities(id) ON DELETE CASCADE,
                FOREIGN KEY(country_id) REFERENCES countries(id) ON DELETE CASCADE)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS cities_states(
                city_id INTEGER,
                state_id INTEGER,
                UNIQUE(city_id, state_id)
                FOREIGN KEY(city_id) REFERENCES cities(id) ON DELETE CASCADE,
                FOREIGN KEY(state_id) REFERENCES states(id) ON DELETE CASCADE)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS city_names_aliases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE COLLATE NOCASE)''')

    cur.execute('''CREATE TABLE IF NOT EXISTS cities_aliases (
                city_id INTEGER,
                alias_id INTEGER,
                UNIQUE(city_id, alias_id),
                FOREIGN KEY(city_id) REFERENCES cities(id) ON DELETE CASCADE,
                FOREIGN KEY(alias_id) REFERENCES city_names_aliases(id) ON DELETE CASCADE)''')

    cur.execute(
        '''CREATE INDEX IF NOT EXISTS countries_iso2_idx ON countries(iso2 COLLATE NOCASE)''')
    cur.execute(
        '''CREATE INDEX IF NOT EXISTS  countries_iso3_idx ON countries(iso3 COLLATE NOCASE)''')

    cur.execute(
        '''CREATE INDEX IF NOT EXISTS country_names_aliases_name_idx ON country_names_aliases(name COLLATE NOCASE)''')

    cur.execute(
        '''CREATE INDEX IF NOT EXISTS  countries_aliases_country_id_idx ON countries_aliases(country_id)''')
    cur.execute(
        '''CREATE INDEX IF NOT EXISTS  countries_aliases_alias_id_idx ON countries_aliases(alias_id)''')

    cur.execute(
        '''CREATE INDEX IF NOT EXISTS  states_name_idx ON states(name COLLATE NOCASE)''')

    cur.execute(
        '''CREATE INDEX IF NOT EXISTS  cities_popoulation_idx ON cities(population)''')

    cur.execute(
        '''CREATE INDEX IF NOT EXISTS city_names_aliases_name_idx ON city_names_aliases(name COLLATE NOCASE)''')

    cur.execute(
        '''CREATE INDEX IF NOT EXISTS  cities_aliases_city_id_idx ON cities_aliases(city_id)''')
    cur.execute(
        '''CREATE INDEX IF NOT EXISTS  cities_aliases_alias_id_idx ON cities_aliases(alias_id)''')

    cur.execute(
        '''CREATE INDEX IF NOT EXISTS  cities_countries_city_id_idx ON cities_countries(city_id)''')
    cur.execute(
        '''CREATE INDEX IF NOT EXISTS  cities_countries_country_id_idx ON cities_countries(country_id)''')

    cur.execute(
        '''CREATE INDEX IF NOT EXISTS  cities_states_city_id_idx ON cities_states(city_id)''')
    cur.execute(
        '''CREATE INDEX IF NOT EXISTS  cities_states_state_id_idx ON cities_states(state_id)''')

    cur.execute(
        '''CREATE INDEX IF NOT EXISTS  timezones_name_idx ON timezones(name COLLATE NOCASE)''')

    cur.execute('''CREATE VIEW IF NOT EXISTS view_search_by_city_name AS
                SELECT
                ct.id id, ct.name name, ctna.name name_alias, ct.population population,
                s.id state_id, s.name state_name,
                c.id country_id, c.name country_name, c.iso2 country_iso2, c.iso3 country_iso3,
                t.name timezone
                FROM cities ct
                INNER JOIN timezones t ON t.id = ct.timezone_id
                INNER JOIN cities_countries cc ON cc.city_id = ct.id
                INNER JOIN countries c ON c.id = cc.country_id
                INNER JOIN cities_states cs ON cs.city_id = ct.id
                INNER JOIN states s ON s.id = cs.state_id
                INNER JOIN cities_aliases cta ON cta.city_id = ct.id
                INNER JOIN city_names_aliases ctna ON ctna.id = cta.alias_id''')

    cur.execute('''CREATE VIEW IF NOT EXISTS view_search_by_country_name AS
        SELECT
        c.id id, c.name name, cna.name name_alias, c.iso2 iso2, c.iso3 iso3
        FROM countries c
        INNER JOIN countries_aliases ca ON ca.country_id = c.id
        INNER JOIN country_names_aliases cna ON cna.id = ca.alias_id''')

    # cur.execute('COMMIT')

    countries_d = {}
    countries_aliases_d = {}
    states_d = {}
    timezones_d = {}
    cities_aliases_d = {}
    city_name_chunks_max = 0

    i = 0
    for _id, city_names, countries, state, population, timezone in get_cities(use_foreign_languages=full):
        if i % 1000 == 0 and i != 0:
            print('Inserted: {} cities'.format(i))
        i += 1
        cids = []
        for country in countries:
            iso2 = country['iso2']
            iso3 = country['iso3']
            country_name = country['name']
            country_name_aliases = country['aliases']

            if iso2 in countries_d:
                cids.append(countries_d[iso2])
                continue

            cur.execute('''INSERT INTO countries (name, iso2, iso3)
                        VALUES (?, ?, ?)''', (country_name, iso2, iso3))

            cid = cur.lastrowid
            countries_d[iso2] = cid
            cids.append(cid)

            for country_name_alias in country_name_aliases:
                if country_name_alias.lower() not in countries_aliases_d:
                    cur.execute('''INSERT INTO country_names_aliases (name)
                        VALUES (?)''', (country_name_alias,))
                    countries_aliases_d[country_name_alias.lower()] = cur.lastrowid

                caid = countries_aliases_d[country_name_alias.lower()]
                cur.execute('''INSERT INTO countries_aliases (country_id, alias_id)
                        VALUES (?, ?)''', (cid, caid))

        sids = []
        for cid in cids:
            if cid not in states_d:
                states_d[cid] = {}
            if state not in states_d[cid]:
                cur.execute('''INSERT INTO states (country_id, name)
                            VALUES (?, ?)''', (cid, state))
                sid = cur.lastrowid
                states_d[cid][state] = sid
            else:
                sid = states_d[cid][state]
            sids.append(sid)

        if timezone not in timezones_d:
            cur.execute('''INSERT INTO timezones (name)
                        VALUES (?)''', (timezone,))
            tid = cur.lastrowid
            timezones_d[timezone] = tid
        else:
            tid = timezones_d[timezone]

        city_name_chunks = city_names['name'].split()
        city_name_chunks_max = max(city_name_chunks_max, len(city_name_chunks))

        cur.execute('''INSERT INTO cities (id, timezone_id, name, population)
                    VALUES (?, ?, ?, ?)''', (_id, tid, city_names['name'], population))

        for city_name_alias in city_names['aliases']:
            if city_name_alias.lower() not in cities_aliases_d:
                cur.execute('''INSERT INTO city_names_aliases (name)
                        VALUES (?)''', (city_name_alias,))
                cities_aliases_d[city_name_alias.lower()] = cur.lastrowid

            cnaid = cities_aliases_d[city_name_alias.lower()]
            cur.execute('''INSERT INTO cities_aliases (city_id, alias_id)
                        VALUES (?, ?)''', (_id, cnaid))

        for cid in cids:
            cur.execute('''INSERT INTO cities_countries (city_id, country_id)
                        VALUES (?, ?)''', (_id, cid))

        for sid in sids:
            cur.execute('''INSERT INTO cities_states (city_id, state_id)
                        VALUES (?, ?)''', (_id, sid))

    cur.execute('''INSERT INTO meta (city_name_chunks_max) VALUES (?)''',
                (city_name_chunks_max,))
    db.commit()
    for row in cur.execute('SELECT COUNT(*) FROM cities'):
        cities_num = row[0]
        if i != cities_num:
            print('Something went wrong, cities inserted is not equal to cities read from file')
        print('Cities inserted: {}. Cities read from file {}'.format(cities_num, i))
    export_db(db, sql_filepath)
    db.close()
