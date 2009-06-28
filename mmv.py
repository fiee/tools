#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Multiple Move

> %s "pattern" "new pattern"

with pattern containing * and ? wildcards,
that get replaced by #1, #2 etc. in new pattern

wildcards match everything besides space
"""
import os, sys, re, glob, unicodedata
try:
	import locale
	locale.setlocale(os.environ['LC_ALL'])
except:
	pass

def normalize(s):
	return unicodedata.normalize('NFC', unicode(s, 'utf-8'))

source_repl = (
	('.', '\\.'),
	('*', '(\\S*)'),
	('?', '(\\S)'),
	#('#', '(\\d)'),
)

reTargetWildcard = re.compile('#(\d+)', re.I|re.U)

os.path.supports_unicode_filenames = True

if len(sys.argv) < 3:
	print __doc__ % sys.argv[0]
	sys.exit(1)
	

for i in (1,2):
	t = sys.argv[i]
	t = t.strip('"')
	sys.argv[i] = t
	
(source, target) = sys.argv[1:3]
source = normalize(source)
target = normalize(target)

sourcelist = glob.glob(source)
sourcelist.sort()

if not sourcelist:
	print u"No files found matching '%s'." % source
	sys.exit(1)

for (s, t) in source_repl:
	source = source.replace(s, t)
target = reTargetWildcard.sub(r'\\g<\1>', target)

reFind = re.compile(source, re.I|re.U)

for s in sourcelist:
	s = normalize(s)
	m = reFind.match(s)
	if m:
		t = reFind.sub(target, s, 1)
		if os.path.exists(t):
			print u"%s -/-> %s : target exists" % (s, t)
		else:
			print u"%s ---> %s" % (s, t)
			os.rename(s, t)