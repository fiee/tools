#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Konvertierung vom MAB-Format in das BibTeX-Format
"""
import os.path, sys, re, string, codecs, latex

AppInfo = """
MAB2Bib 0.2a : bibliographischer Konverter von MAB nach BibTeX

(r) 2005 by fiëé TeXnique, Henning Hraban Ramm, hraban@fiee.net
im Auftrag von Uwe Jochum, Uni Konstanz, uwe.jochum@uni-konstanz.de
LaTeX-Codec von D. Eppstein
Lizenz: Python-Lizenz (http://python.org/doc/Copyright.html)
"""

AppHelp = """Aufruf: [python] mab2bib.py <MAB-Datei> [<BibTeX-Datei>]
Ist keine Ausgabedatei angegeben, wird an die Eingabedatei '.bib' angehängt.

Die Datei latex.py muss im gleichen Verzeichnis liegen!
"""

class Datensatz(dict):
    """Datensatz einer bibliografischen Datenbank
    Als Felder (Schlüssel) werden die MAB-felder verwendet, weil sie genauer sind
    """

    # Zuordnung von MAB-Feldern auf BibTeX-Felder
    mab2bib = {
        'id' : None,
        '081': 'title',
        '089': 'series',
        '100': 'author',
        '100b': 'editor',
        '100c': 'editor',
        '100e': 'author',
        '100f':  'author',
        '104': 'author',
        '104a': 'author',
        '104b': 'editor',
        '104c': 'editor',
        '104e': 'author',
        '104f': 'author',
        '108': 'author',
        '108a': 'author',
        '108b': 'editor',
        '108c': 'editor',
        '108e': 'author',
        '108f': 'author',
        '112': 'author',
        '112a': 'author',
        '112b': 'editor',
        '112c': 'editor',
        '112e': 'author',
        '112f': 'author',
        '200': 'institution',
        '200b': 'title',
        '204': 'institution',
        '304': 'title',
        '310': 'title',
        '331': 'title',
        '333': 'author',
        '334': 'annote',
        '335': 'title',
        '359': 'note',
        '376': 'journal',
        '400': 'edition',
        '403': 'edition',
        '410': 'address',
        '412': 'publisher',
        '415': 'address',
        '417': 'publisher',
        '425': 'year',
        '433': 'pages',
        '434': 'annote',
        '451': 'series',
        '454': 'series',
        '455': 'volume',
        '456': 'volume',
        '501': 'annote',
        '519': 'type',
        '531': 'copyright',
        '533': 'annote',
        '540': 'ISBN',
        '540a': 'ISBN',
        '540b': 'ISBN',
        '542': 'ISSN',
        '544': 'LCCN',
        '590': 'howpublished',
        '596': 'howpublished',
        '25': None
    }

    # Trennzeichen zwischen gleichartigen Einträgen in BiBTeX
    glue = {
        'default': '; ',
        'author':' and ',
        'editor':' and ',
        'title':'. ',
        'series': '/',
    }

    # Übersetzung von MAB-Zeichen in TeX-Zeichen
    # Achtung, reguläre Ausdrücke!
    # das meiste wird von latex.py erledigt!
    tex_trans = {
        '\xAC' : ' ', # Negationszeichen zur Bezeichnung eines Nicht-Sortierwortes(?) entfernen
        '&lt;' : '', # werden die spitzen Klammern gebraucht?
        '&gt;' : '',
        '\.{2,}' : '\\dots',
        ' - ' : ' -- ',
        '\s+' : ' '
    }

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)

    def __setitem__(self, key, value):
        if key in self.mab2bib.keys():
            dict.__setitem__(self, key, value)
        else:
            print "Unbekannter Schlüssel '%s' (Wert: '%s')" % (key, value)

    def update(self, updatedict):
        "überschrieben, damit das eigene __setitem__ verwendet wird"
        for key in updatedict.keys():
            self[key] = updatedict[key]

    def translate(self, s, table, deletechars=None):
        "ersetzt Sonderzeichen usw.; ähnlich string.translate"
        for k in self.tex_trans.keys():
            s = re.sub(k, self.tex_trans[k], s)
        s = unicode(string.strip(s), 'latin-1').encode('latex') # evtl. mac-roman
        return s

    def BibTeXdict(self):
        btd = {}
        felder = self.keys()
        felder.sort()
        for key in felder:
            bkey = self.mab2bib[key]
            if not bkey: continue
            val = self.translate(self[key], self.tex_trans)
            if self.glue.has_key(bkey):
                glue = self.glue[bkey]
            else:
                glue = self.glue['default']
            if btd.has_key(bkey):
                btd[bkey] = string.join((btd[bkey], val), glue)
            else:
                btd[bkey] = val
        return btd

    def toBibTeX(self):
        erg = []
        btd = self.BibTeXdict()
        for key in btd.keys():
            erg.append("%s\t= {%s}" % (key, btd[key]))
        return "@book { %s,\n%s\n}\n\n" % (self['id'], string.join(erg, ",\n"))



class MABfile(file):
    """?"""

    reMABzeile = re.compile('^(?P<key>\d+\w?)\s+(?P<val>.+)$', re.IGNORECASE)
    reLeerzeile = re.compile('^\s*$')

    def process(self):
        """Lese MAB-Datei und erzeuge Liste von Datensätzen als self.daten"""
        self.daten = []
        dsno = -1
        inds = False
        for zeile in self.readlines():
            if self.reLeerzeile.match(zeile):
                if inds: inds = False
                continue
            zeile = string.strip(zeile)
            m = self.reMABzeile.match(zeile)
            if not m:
                print "Ungültige MAB-Zeile: %s" % zeile
                continue
            key = string.lower(m.group('key'))
            val = string.strip(m.group('val'))
            if not inds:
                # neuer Datensatz
                inds = True
                dsno += 1
                self.daten.append(Datensatz())
                id = string.replace(string.lower(string.split(val, None, 2)[0]), ',', '')
                self.daten[dsno]['id'] = id + str(dsno)
            self.daten[dsno][key] = val

    def writeBibTeXfile(self, dateiname):
        if not hasattr(self, 'daten'): self.process()
        btf = open(dateiname, 'w')
        for ds in self.daten:
            btf.write(ds.toBibTeX())
        btf.close()


def help():
    print AppInfo
    print AppHelp
    sys.exit(0)

if __name__=='__main__':
    if len(sys.argv) < 2: help()
    mabname = sys.argv[1]
    if not os.path.isfile(mabname):
        print "MAB-Datei '%s' nicht gefunden!" % mabfile
        sys.exit(1)
    bibname = mabname+'.bib'
    if len(sys.argv) > 2:
        bibname = sys.argv[2]

    mabfile = MABfile(mabname, 'r')
    mabfile.writeBibTeXfile(bibname)
    mabfile.close()
