#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, shutil, unicodedata


ersetzungen = {
	'ä' : 'ae',
	'ö' : 'oe',
	'ü' : 'ue',
	'ß' : 'ss',
	' ' : '_',
	'__' : '_',
	'..' : '.',
}

illegals = "'´`/\\§$#@?!<>\""

def cleanfilename(filename):
	filename = unicodedata.normalize('NFC', unicode(filename, 'utf-8')).encode('utf-8').strip().lower()
	for char in illegals:
		filename = filename.replace(char, '')
	for key in ersetzungen:
		filename = filename.replace(key, ersetzungen[key])
	return filename


top = sys.argv[1]

for root, dirs, files in os.walk(top):
	for f in files:
		clean = cleanfilename(f)
		print root, "\t", f, "\t", clean
		shutil.move(os.path.join(root, f), os.path.join(root, clean))
	if len(sys.argv) > 2:
		for x in range(len(dirs)):
			d = dirs[x]
			clean = cleanfilename(d)
			dirs[x] = clean
			print root, "\t", d, "\t", clean
			shutil.move(os.path.join(root, d), os.path.join(root, clean))
