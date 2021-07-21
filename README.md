# Geonames data to sqlite

Data obtained from http://download.geonames.org/export/dump/

## How to get the data

### Way 1
From repo

```bash
git clone https://github.com/tchar/cities-geonames
cd cities-geonames
# For data without language aliases
python main.py
# For data with language aliases
python main.py --full
```
Generated sqlite and sql dump will be at `cities-geonames/out`

### Way 2
Fething zip data from github and creating the database on the fly

For data without language aliases
```bash
# Set your prefered database file path i.e /home/your-username/cities.sqlite3
export DB_PATH="~/cities.sqlite3"

python -c "import os,os.path as p,urllib.request as r,zipfile as z,io,sqlite3 as s;db_path=p.abspath(p.expanduser(os.environ.get('DB_PATH', 'cities.sqlite3')));s.connect(db_path).executescript(z.ZipFile(io.BytesIO(r.urlopen('https://github.com/tchar/cities-geonames/raw/master/zip/cities.zip').read())).read('cities.sql').decode()).close() or print('Saved to {}'.format(db_path)) if 'DB_PATH' in os.environ else print('Run with DB_PATH in environement variables')"
```

For data with language aliases
```bash
# Set your prefered database file path i.e /home/your-username/cities.sqlite3
export DB_PATH="~/cities.sqlite3"

python -c "import os,os.path as p,urllib.request as r,zipfile as z,io,sqlite3 as s;db_path=p.abspath(p.expanduser(os.environ.get('DB_PATH', 'cities.sqlite3')));s.connect(db_path).executescript(z.ZipFile(io.BytesIO(r.urlopen('https://github.com/tchar/cities-geonames/raw/master/zip/cities-full.zip').read())).read('cities.sql').decode()).close() or print('Saved to {}'.format(db_path)) if 'DB_PATH' in os.environ else print('Run with DB_PATH in environement variables')"
```

## Querying

You can get cities info from the already created view like follows. It should be pretty fast on indexes. Indexed fields are ids and names.
Aliases are `COLLATE NOCASE` so should be case insensitive even without using `LIKE` (e.g using country iso2 with lowercase instead of upercase)

Here is an query using indexes to get city info for the 10 best matches based on population
```sql
SELECT name, population, country_name, timezone
FROM view_search_by_city_name
WHERE name_alias LIKE 'ath%'
GROUP BY id, country_id, state_id
ORDER BY (name_alias = 'ath') DESC, (name LIKE 'ath%') DESC, population DESC
LIMIT 4
```
Results fetched in ~3ms/xms (without/with extra languages)
| name          |population | country_name  | state_name    | timezone          |
| -----------   | --------- | --------      | ----------    | --------          |
| Ath           | 26681     | Belgium       | WAL           | Europe/Brussels   |
| Athens        | 664046    | Greece        | ESYE31        | Europe/Athens     |    
| Athens        | 116714    | United States | GA            | America/New_York  |
| Ath Thawrah   | 87880     | Syria         | 04            | Asia/Damascus     |


Here is an query using indexes to get countries
```sql
SELECT name, iso2, iso3
FROM view_search_by_country_name
WHERE (
    name_alias LIKE 'In%' OR
    iso2 = 'in' OR iso3 ='IND'
)
GROUP BY id
ORDER BY (iso2 = 'IN' OR iso3 = 'ind') DESC
```
Results without extra languages (~5ms)
| name      | iso2  | iso3  |
| --------- | ----- | ----- |
| India     | IN    | IND   |
| Indonesia | ID    | IDN   |

Results with extra languages (~20 ms 46/rows)
Include much more countries as there are many countries starting with `in` in other languages

If you want to filter out cities from specific countries with a condition of more than just country `iso2` and `iso3`
you can combine these two queries like this:
```sql
-- Search for cities starting with ath in countries starting with gr or be
-- Sort results by iso2 = 'GR' city name (not city name alias) matches 'Ath' and population
SELECT city.name, city.population, city.timezone
FROM (
	SELECT * FROM view_search_by_city_name
	WHERE name_alias LIKE 'ath%'
	GROUP BY id, country_id, state_id
) city
INNER JOIN (
	SELECT * FROM view_search_by_country_name
	WHERE name_alias LIKE 'gr%' OR name_alias LIKE 'be%'
	GROUP BY id
) country ON country.id = city.country_id
ORDER BY (country.iso2 = 'GR') DESC, (city.name LIKE 'ath%') DESC, city.population DESC
```
Results without extra languages (~9ms)
| name      |population | timezone          |
| --------- | -----     | -------------     | 
| Athens    | 664046    | Europe/Athens     |
| Ath       | 26681     | Europe/Brussels   |

Results with extra languages (~9ms)
Includes cities from UK as it has an alias as Great Britain. Also Oxford has an alias starting with `ath`
| name      |population | timezone          |
| --------- | -----     | -------------     | 
| Athens    | 664046    | Europe/Athens     |
| Ath       | 26681     | Europe/Brussels   |
| Atherton  | 20149     | Europe/London     |
| Oxford    | 171380    | Europe/London     |

## Extra queries with extra languages
If you used the full version with name aliases in every language queries like this should work

```sql
-- Search for countries starting with 'भा' in Hindu
SELECT name, iso2, iso3, name_alias
FROM view_search_by_country_name
WHERE name_alias LIKE 'भा%'
GROUP BY id
```
Results fetched in ~5ms with the extra languages db
| name      | iso2  | iso3  | name_alias |
| --------- | ----- | ----- | ---        |
| India     | IN    | IND   | भारत        |
| Vanuatu   | VU    | VUT   | भानआत      |

Or
```sql
-- Search for Athens Greece in Farsi
SELECT city.name, city.population, city.timezone, city.name_alias
FROM (
	SELECT * FROM view_search_by_city_name
	WHERE name_alias LIKE 'آتن%'
	GROUP BY id, country_id, state_id
) city
INNER JOIN (
	SELECT * FROM view_search_by_country_name
	WHERE name_alias LIKE 'یونان%'
	GROUP BY id
) country ON country.id = city.country_id
ORDER BY (city.name_alias = 'آتن') DESC, population DESC
```
Results fetched in ~5ms with the extra languages db
| name      |population | timezone          | name_alias |
| --------- | -----     | -------------     | ----       |
| Athens    | 664046    | Europe/Athens     | آتن        |
