#!/usr/bin/env python3
import sys
import datetime
import arrow

ZODIAC = (
	('21.01.', '19.02.', 'Wassermann', 'rebellisch, eigenwillig, gutmütig, tolerant'),
	('20.02.', '20.03.', 'Fische', 'hilfsbereit, sensibel, selbstmitleidig'),
	('21.03.', '20.04.', 'Widder', 'leidenschaftlich, abenteuerlustig, egoistisch, aufbrausend'),
	('21.04.', '20.05.', 'Stier', 'stur, faul, zielstrebig, zuverlässig'),
	('21.05.', '21.06.', 'Zwilling', 'schlagfertig, intelligent, ungeduldig, untreu'),
	('22.06.', '22.07.', 'Krebs', 'sanftmütig, treu, fürsorglich, feinfühlig'),
	('23.07.', '23.08.', 'Löwe', 'stolz, hochmütig, arrogant, gesellig, großherzig, aufmerksamkeitsbedürftig'),
	('24.08.', '23.09.', 'Jungfrau', 'zuverlässig, ehrlich, diszipliniert, prüde, unnahbar'),
	('24.09.', '23.10.', 'Waage', 'harmoniebedürftig, ästhetisch, gerechtigkeitsliebend'),
	('24.10.', '22.11.', 'Skorpion', 'willensstark, analytisch, loyal, rachsüchtig, nachtragend, skrupellos'),
	('23.11.', '21.12.', 'Schütze', 'fröhlich, weltoffen, optimistisch, angeberisch, maßlos'),
	('22.12.', '20.01.', 'Steinbock', 'fleißig, ehrgeizig, verantwortungsbewusst, geduldig, langweilig, spießig'),
)

# Erdzweige. (Jahreszahl + 9) % 12
CHINESE = (
    ('Ratte', 'gesellig, aktiv, aggressiv'), # 2008
    ('Büffel', 'ruhig, besonnen'),
    ('Tiger', 'Führungsqualitäten, selbstsicher, mutig'),
    ('Hase', 'Lebenskünstler, konfliktscheu'),
    ('Drache', 'selbstbewusst, zuverlässig, mutig'),
    ('Schlange', 'geheimnisvoll, zurückhaltend, empathisch'),
    ('Pferd', 'kräftig, heiter, redselig'),
    ('Ziege', 'liebenswürdig, gütig, scheu'),
    ('Affe', 'intelligent, redegewandt'),
    ('Hahn', 'Beobachter, intuitiv, aufrichtig'),
    ('Hund', 'treu, ehrlich, zuverlässig'),
    ('Schwein', 'gemütlich, friedlich, tolerant'),
)

# Himmelsstamm. (Jahreszahl + 7)[-1]
ELEMENTS = (
	('Holz', 'Yang'),
	('Holz', 'Yin'),
	('Feuer', 'Yang'),
	('Feuer', 'Yin'),
	('Erde', 'Yang'),
	('Erde', 'Yin'),
	('Metall', 'Yang'),
	('Metall', 'Yin'),
	('Wasser', 'Yang'),
	('Wasser', 'Yin'),
)

NEWYEAR = {
	1936: ('Ratte', '1936-01-24'),
	1937: ('Büffel', '1937-02-11'),
	1938: ('Tiger', '1938-01-31'),
	1939: ('Hase', '1939-02-19'),
	1940: ('Drache', '1940-02-08'),
	1941: ('Schlange', '1941-01-27'),
	1942: ('Pferd', '1942-02-15'),
	1943: ('Ziege', '1943-02-05'),
	1944: ('Affe', '1944-01-25'),
	1945: ('Hahn', '1945-02-13'),
	1946: ('Hund', '1946-02-02'),
	1947: ('Schwein', '1947-01-22'),
	1948: ('Ratte', '1948-02-10'),
	1949: ('Büffel', '1949-01-29'),
	1950: ('Tiger', '1950-02-17'),
	1951: ('Hase', '1951-02-06'),
	1952: ('Drache', '1952-01-27'),
	1953: ('Schlange', '1953-02-14'),
	1954: ('Pferd', '1954-02-03'),
	1955: ('Ziege', '1955-01-24'),
	1956: ('Affe', '1956-02-12'),
	1957: ('Hahn', '1957-01-31'),
	1958: ('Hund', '1958-02-18'),
	1959: ('Schwein', '1959-02-08'),
	1960: ('Ratte', '1960-01-28'),
	1961: ('Büffel', '1961-02-15'),
	1962: ('Tiger', '1962-02-05'),
	1963: ('Hase', '1963-01-25'),
	1964: ('Drache', '1964-02-13'),
	1965: ('Schlange', '1965-02-02'),
	1966: ('Pferd', '1966-01-21'),
	1967: ('Ziege', '1967-02-09'),
	1968: ('Affe', '1968-01-30'),
	1969: ('Hahn', '1969-02-17'),
	1970: ('Hund', '1970-02-06'),
	1971: ('Schwein', '1971-01-27'),
	1972: ('Ratte', '1972-02-15'),
	1973: ('Büffel', '1973-02-03'),
	1974: ('Tiger', '1974-01-23'),
	1975: ('Hase', '1975-02-11'),
	1976: ('Drache', '1976-01-31'),
	1977: ('Schlange', '1977-02-18'),
	1978: ('Pferd', '1978-02-07'),
	1979: ('Ziege', '1979-01-28'),
	1980: ('Affe', '1980-02-16'),
	1981: ('Hahn', '1981-02-05'),
	1982: ('Hund', '1982-01-25'),
	1983: ('Schwein', '1983-02-13'),
	1984: ('Ratte', '1984-02-02'),
	1985: ('Büffel', '1985-02-20'),
	1986: ('Tiger', '1986-02-09'),
	1987: ('Hase', '1987-01-29'),
	1988: ('Drache', '1988-02-17'),
	1989: ('Schlange', '1989-02-06'),
	1990: ('Pferd', '1990-01-27'),
	1991: ('Ziege', '1991-02-15'),
	1992: ('Affe', '1992-02-04'),
	1993: ('Hahn', '1993-01-23'),
	1994: ('Hund', '1994-02-10'),
	1995: ('Schwein', '1995-01-31'),
	1996: ('Ratte', '1996-02-19'),
	1997: ('Büffel', '1997-02-07'),
	1998: ('Tiger', '1998-01-28'),
	1999: ('Hase', '1999-02-16'),
	2000: ('Drache', '2000-02-05'),
	2001: ('Schlange', '2001-01-24'),
	2002: ('Pferd', '2002-02-12'),
	2003: ('Ziege', '2003-02-01'),
	2004: ('Affe', '2004-01-22'),
	2005: ('Hahn', '2005-02-09'),
	2006: ('Hund', '2006-01-29'),
	2007: ('Schwein', '2007-02-18'),
	2008: ('Ratte', '2008-02-07'),
	2009: ('Büffel', '2009-01-26'),
	2010: ('Tiger', '2010-02-14'),
	2011: ('Hase', '2011-02-03'),
	2012: ('Drache', '2012-01-23'),
	2013: ('Schlange', '2013-02-10'),
	2014: ('Pferd', '2014-01-31'),
	2015: ('Ziege', '2015-02-19'),
	2016: ('Affe', '2016-02-08'),
	2017: ('Hahn', '2017-01-28'),
	2018: ('Hund', '2018-02-16'),
	2019: ('Schwein', '2019-02-05'),
	2020: ('Ratte', '2020-01-25'),
	2021: ('Büffel', '2021-02-12'),
	2022: ('Tiger', '2022-02-01'),
}

def zodiacsign(birthday):
    year = birthday.year
    stb1 = arrow.get('%s-01-20' % year)
    stb2 = arrow.get('%s-12-22' % year)
    if birthday <= stb1 or birthday >= stb2:
        # Steinbock
        sign = ZODIAC[11]
        return sign[2], sign[3]
    silvester = arrow.get('%s-12-31' % year)
    for sign in ZODIAC:
        start = arrow.get('%s%s' % (sign[0], str(year)), 'DD.MM.YYYY')
        end = arrow.get('%s%s' % (sign[1], str(year)), 'DD.MM.YYYY')
        if ((birthday >= start) and (birthday <= end)):
            return sign[2], sign[3]
    return 'Unbekannt'

def chinesesign(birthday):
    """
    returns year, element, yin/yang, animal, features
    """
    year = birthday.year
    NY = NEWYEAR[year]
    nyd = arrow.get(NY[1])
    if birthday < nyd:
        year -= 1
    ret = [year, ]
    index = int(str(year + 9)[-1]) -1
    ret.extend(ELEMENTS[index])
    index = (year + 9) % 12
    ret.extend(CHINESE[index - 1])
    return ret

def humanizedelta(td):
    years = td.days / 365
    months = (td.days % 365) / 30
    return '%d Jahre, %d Monate' % (years, months)

if len(sys.argv) < 2:
    print('not enough values: [today] birthday')
    sys.exit(1)
elif len(sys.argv) == 2:
    today = arrow.now()
    bday = arrow.get(sys.argv[1])
else:
    today = arrow.get(sys.argv[1])
    bday = arrow.get(sys.argv[2])

delta = today - bday
print(humanizedelta(delta))
print(zodiacsign(bday))
print(chinesesign(bday))
