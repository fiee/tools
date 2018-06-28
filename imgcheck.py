#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from __future__ import print_function
import sys, os, unicodedata
import PIL.Image as Image

imgexts = ('.jpg', '.tif', '.pdf', '.bmp', '.pct', '.tga', '.jpeg', '.tiff', '.pict')
txtexts = ('.doc', '.rtf', '.txt', '.xml', '.html', '.htm', '.indd', '.pdf')

def compose(path):
    """
    MacOS X verwendet decomposed UTF-8 im Dateisystem; diese Funktion erzeugt daraus "normales" UTF-8
    """
    #if type(path) is not unicode:
    #    path = unicode(path, 'utf-8')
    return unicodedata.normalize('NFC', path)

def decompose(path):
    """
    MacOS X braucht decomposed UTF-8 im Dateisystem
    """
    if type(path) is not unicode:
        path = unicode(path, 'utf-8')
    return unicodedata.normalize('NFD', path)

def px2cm(px, dpi=300):
    """
    Umrechnung von Pixel in Zentimeter bei der angegebenen Auflösung
    """
    return px * 2.54 / dpi

def checkimage(filename, path='.'):
    filename = compose(filename)
    path = compose(path)
    filepath = os.path.join(path, filename)
    out = ''
    if not os.path.isfile(filepath): return out
    try:
        img = Image.open(filepath)
        (x, y) = img.size
        (xcm, ycm) = map(px2cm, (x,y))
        out += u"%s\n\tFarbmodus: %s\tDateiformat: %s\n\t%4d x %4d px\n" % (filename, img.mode, img.format, x, y)
        out += u"\tbei 300 dpi = %02.2f x %02.2f cm (Optimalgröße)\n\tbei 200 dpi = %02.2f x %02.2f cm (Maximalgröße)\n" \
        %(px2cm(x,300), px2cm(y,300), px2cm(x,200), px2cm(y,200))
    except Exception as ex:
        out += u"%s\tist kein Bild\t%s\n" % (filename, ex)
    return out

path = '.'
if len(sys.argv) > 1:
    path = sys.argv[1]

if not os.path.isdir(path):
    print("%s ist kein Verzeichnis!" % path)
    sys.exit(1)

out = ''
for root, dirs, files in os.walk(path):
    try:
        root = compose(root)
        pfadname = "\n[%s]\n" % root.strip('.').strip('/')
    except UnicodeDecodeError as ex:
        print(ex)
        print(root)
        sys.exit()
    bilder = 0
    subout = ''
    for filename in files:
        if filename.startswith('.'): continue
        (basename, ext) = os.path.splitext(filename)
        if not ext in txtexts:
            bilder += 1
            subout += checkimage(filename, root)
    if bilder > 0:
        out += pfadname + subout
print(out)
