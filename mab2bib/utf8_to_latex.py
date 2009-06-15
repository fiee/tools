#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Universelle Textcodierung
2009-06-15 by Henning Hraban Ramm, fiﾑe virtuﾑlle

quellcodierung_to_zielcodierung.py [Optionen] Quelldatei [Zieldatei]

Es kﾚnnen auch ganze Verzeichnisse bearbeitet werden.

Die gewﾟnschte Codierung wird aus dem Dateinamen ermittelt.
Mﾚgliche Werte sind z.B.
latin1 (iso-8859-1), utf8, macroman, latex (sofern latex.py vorhanden ist)

Optionen:
--filter=Dateiendung
--overwrite          (sonst wird die Originaldatei gesichert)
--hidden             (sonst werden versteckte Dateien ignoriert)
"""

import os, os.path, sys, codecs, getopt, shutil
try:
    import latex
except:
    pass

modes = ('filter', 'overwrite', 'hidden')
mode = {}

def help(message=""):
    print message
    print __doc__
    sys.exit(1)

def backup(datei):
    original = datei
    pfad, datei = os.path.split(datei)
    datei, ext = os.path.splitext(datei)
    count = 0
    while os.path.exists(os.path.join(pfad, u"%s.%d%s" % (datei, count, ext))):
        count += 1
    neudatei = os.path.join(pfad, u"%s.%d%s" % (datei, count, ext))
    print u"Sichere %s als %s" % (original, neudatei)
    shutil.copy(original, neudatei)
    return neudatei

def is_hidden(datei):
    return (datei.startswith('.') or os.sep+'.' in datei)

def convert(source, target, so_enc, ta_enc):
    from_exists = os.path.exists(source)
    to_exists = os.path.exists(target)
    from_isdir = os.path.isdir(source)
    to_isdir = os.path.isdir(target)
    from_path, from_name = os.path.split(source)
    to_path, to_name = os.path.split(target)
    #from_name = os.path.basename(source)
    #to_name = os.path.basename(target)

    if not from_exists:
        help(u"Quelle '%s' nicht gefunden!" % from_name)

    if from_isdir:
        if is_hidden(source) and not mode['hidden']:
            print u"Ignoriere verstecktes Verzeichnis %s" % source
            return
        if not to_isdir:
            help(u"Wenn die Quelle ein Verzeichnis ist, muss auch das Ziel ein Verzeichnis sein!")
        print u"Verarbeite Verzeichnis %s" % source
        dateien = os.listdir(source)
        #if not mode['hidden']:
        #    dateien = [d for d in dateien if not is_hidden(d)]
        if mode['filter']:
            dateien = [d for d in dateien if d.endswith(mode['filter'])]
        for datei in dateien:
            s = os.path.join(source, datei)
            t = os.path.join(target, datei)
            convert(s, t, so_enc, ta_enc)
    else:
        if is_hidden(from_name) and not mode['hidden']:
            print u"Ignoriere versteckte Datei %s" % source
            return
        if to_isdir:
            target = os.path.join(target, from_name)
        if not mode['overwrite']:
            if source==target:
                source=backup(source)
            elif os.path.exists(target):
                backup(target)
        print u"Konvertiere %s (%s)\n\tnach %s (%s)" % (source, so_enc, target, ta_enc)
        so_file = file(source, "rU")
        lines = so_file.readlines()
        so_file.close()
        ta_file = file(target, "w")
        for l in lines:
            ta_file.write(unicode(l, so_enc).encode(ta_enc))
        ta_file.close()
        

opts, args = getopt.getopt(sys.argv[1:], "ohf:", ["overwrite","hidden","filter="])

if len(args)<1:
    help("Zu wenige Parameter angegeben!")

for m in modes:
    mode[m] = False
    for (o, a) in opts:
        if o=='-'+m[0] or o=='--'+m:
            if a:
                print u"Modus %s = %s" % (m, a)
            else:
                a = True
                print u"Modus %s aktiv" % m
            mode[m] = a

#print "modes:", mode
#print "opts :", opts
#print "args :", args

# gewﾟnschte Codierung aus dem Dateinamen ablesen
scriptname = os.path.splitext(os.path.basename(sys.argv[0]))[0]
from_enc, to_enc = scriptname.split("_to_")

from_name = to_name = args[0]
if len(args)>1: to_name = args[1]

convert(from_name, to_name, from_enc, to_enc)
    