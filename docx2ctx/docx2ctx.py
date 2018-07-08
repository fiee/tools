#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convert from MS Word DOCX to ConTeXt source
(c) 2018 Henning Hraban Ramm
License: chose one of BSD, MIT, GPL3+, LGPL
"""
import os
from collections import defaultdict
import re
import logging
import zipfile
import xml.etree.ElementTree as ET
from xml.sax import make_parser, handler
import begin # see http://begins.readthedocs.io/

def constant_factory(value):
	return lambda: value

DEFAULT_LANGUAGE = 'de' # TODO: check locale

SECTIONS = 'paragraph chapter section subsection subsubsection subsubsubsection'.split()

SECTION_MAP = { # Style name to section level
	# These are still only German names, additions welcome
	'Titel': 'chapter',
	'Untertitel': 'section',
	'Berschrift1': 'chapter',
	'Berschrift2': 'section',
	'Berschrift3': 'subsection',
	'Berschrift4': 'subsubsection',
	'Berschrift5': 'subsubsubsection',
}

STYLE_MAP = {
	# Word tag: ('ConTeXt start', attr)
	# ConTeXt command is always closed with }
	# attr is True (no parameter) or a string (one parameter, %s)
	'b': ('\\important{', True),
	'i': ('\\emph{', True),
	'u': ('\\underbar{', True),
	'smallCaps': ('\\scaps{', True),
	'strike': ('\\overstrike{', True),
	'color': ['\\color[%s]{', 'val'],
	'lang': ['{\\language[%s]', 'val'],
	'highlight': ['\\H%s{', 'val'],
	'super': ('\\high{', True),
	'sub': ('\\low{', True),
	'rFonts': ['{\\F%s{}', 'val'],
}

PREAMBLE = """
\\definehighlight[emph][style=italic]
\\definehighlight[important][style=bold]
\\definehighlight[scaps][style=\\sc]
"""

QUOTABLES = '{}$&%'

def texquote(text):
	for c in QUOTABLES:
		text = text.replace(c, '\\'+c)
	return text


class ContextHandler(handler.ContentHandler):
	def __init__(self, **options):
		self.options = options or defaultdict(str)
		self.doctype = 'component' # or text (\starttext or \startcomponent)
		self.elcount = defaultdict(int) # depth, not used ATM
		self.allelements = set() # not used ATM
		self.header = '\\start%s\n' % self.doctype
		self.text = '' # complete text
		self.section = 0 # section level
		self.pText = '' # paragraph text
		self._pPr = defaultdict(constant_factory(False)) # paragraph formatting
		self._rPr = defaultdict(constant_factory(False)) # textrun formatting
		self._numPr = defaultdict(constant_factory(False)) # enumeration
		self.prev_enum = 0 # enum level of previous par
		self.enum = 0 # enum level
		self.elhier = [] # element hierarchy
		self.references = defaultdict(list)
		self.inRef = '' # we're within reference type ''
		self.image = {} # current image
		self.links = [] # list of external references incl. images
		self.metadata = defaultdict(str)
		
		if self.options['colors'] is False:
			del STYLE_MAP['color']
			del STYLE_MAP['highlight']
		if self.options['fonts'] is False:
			del STYLE_MAP['rFonts']
		
	def startDocument(self):
		self.metadata['language'] = self.metadata['language'].split('-')[0]
		if self.options['template'] == 'empty':
			if self.doctype == 'component':
				name = self.metadata['title'].replace(' ', '_')
				self.header = '\\startcomponent c_%s\n' % name
				self.header += '\\product prd_\n\\project prj_\n'
			self.header += '\n\\setupinteraction[\n' + \
				'\ttitle={%(title)s},\n' + \
				'\tsubtitle={%(subject)s},\n' + \
				'\tkeywords={%(keywords)s},\n' + \
				'\tauthor={%(creator)s},\n' + \
				'\tdescription={%(description)s},\n' + \
				'\t]\n' + \
				'\\mainlanguage[%(language)s]\n'
			self.header = self.header % self.metadata
			self.header += PREAMBLE
		else:
			self.header = ''
		
	def startElement(self, name, attrs):
		self.elcount[name] += 1
		self.allelements.add(name)
		self.elhier.append(name)
		tag = name.replace('w:', '').replace(':', '_')
		if tag in ('footnote', 'endnote', 'comment'):
			if self.options[tag+'s'] is False:
				return
			#id = int(attrs['w:id'])
			self.references[tag].append('')
			self.inRef = tag
		elif tag in ('footnoteReference', 'endnoteReference', 'commentReference'):
			tag = tag.replace('Reference','')
			if self.options[tag+'s'] is False:
				return
			self.noteReference(tag, attrs)
		elif tag in STYLE_MAP:
			if 'w:val' in attrs:
				val = attrs['w:val']
				if val in ('false', 'auto', 'none'):
					return
			elif 'w:ascii' in attrs: # fonts
				val = attrs['w:ascii'].replace(' ', '')
			if tag == 'lang':
				val, _ = val.split('-')
			style = STYLE_MAP[tag]
			if type(style[1]) is str:
				style[1] = val
			self.setStyle(tag, style[1])
			if tag in ('color', 'highlight'):
				setup = '\\definecolor[%s][h=%s]\n' % (val, val)
				if not setup in self.header:
					self.header += setup
				if tag == 'highlight':
					setup = '\\definehighlight[H%s][background=color,backgroundcolor=%s]\n' % (val, val)
					if not setup in self.header:
						self.header += setup
			elif tag == 'rFonts':
				setup = '\\definefont[F%s][%s*default]\n' % (val, val.lower())
				if not setup in self.header:
					self.header += setup
		elif hasattr(self, tag):
			logging.debug('%s %s', tag, attrs.keys())
			try:
				getattr(self, tag)(attrs)
			except TypeError as ex:
				logging.error(tag)
				logging.exception(ex)
	
	def characters(self, content):
		self.pText += texquote(content)
	
	def p(self, attrs):
		self.pText = ''
		self._pPr = defaultdict(constant_factory(False))
		#self.text += '\n\\startparagraph\n'
	
	def p_end(self):
		if not self.pText.strip():
			return
		style = self._pPr['style'] or ''
		if self._pPr['b']: # whole paragraph is bold: probably a title
			if self.section > 0:
				self.text += '\n\\stop%s\n' % SECTIONS[self.section]
			if self.section < 2:
				self.section += 1
			#self.pText = self.pText.replace('\\important', '')
			self.pText = re.sub(r'\\important\{(.*?)\}', r'\1', self.pText)
			self.text += '\n\\start%s[title={%s}]\n' % (SECTIONS[self.section], self.pText)
		elif style in SECTION_MAP: # it's a title style
			if self.prev_enum:
				self.text += '\\stopitemize\n'
				self.prev_enum = 0
				self.enum = 0
			cur_sec = SECTION_MAP[style]
			cur_sec_id = SECTIONS.index(cur_sec)
			if self.section >= cur_sec_id:
				# close previous section
				self.text += '\n\\stop%s\n' % SECTIONS[self.section]
			self.section = cur_sec_id
			self.text += '\n\\start%s[title={%s}]\n\n' % (cur_sec, self.pText)
		elif self._numPr['numId'] and int(self._numPr['numId']) > 1:
			if not self.prev_enum or self.prev_enum < self.enum:
				self.enum += 1
				self.text += '\\startitemize[]\n'
			self.text += '\\startitem %% %s, %d, %d\n' % (style, self._numPr['numId'], self._numPr['ilvl'])
			self.text += self.pText
			self.text += '\\stopitem\n'
			self.prev_enum = self.enum
		elif 'w:tc' in self.elhier:
			# within table cell
			self.text += '%% %s\n%s' % (style, self.pText)
		else:
			if self.prev_enum:
				self.text += '\\stopitemize\n'
				self.prev_enum = 0
				self.enum = 0
			self.text += '\n\\startparagraph %% %s\n' % style
			self.text += self.pText
			self.text += '\n\\stopparagraph\n'
		self._numPr = defaultdict(constant_factory(False))
	
	def r(self, attrs):
		self._rPr = defaultdict(constant_factory(False))

	def t(self, attrs):
		for key in self._rPr:
			if self._rPr[key] is True:
				if key == 'baseline':
					continue
				self.pText += STYLE_MAP[key][0]
			elif self._rPr[key]:
				self.pText += STYLE_MAP[key][0] % self._rPr[key]

	def t_end(self):
		for key in self._rPr:
			if key == 'baseline':
				continue
			self.pText += '}'
	
	def setStyle(self, name, val=True):
		if 'w:pPr' in self.elhier:
			self._pPr[name] = val
		elif 'w:rPr' in self.elhier:
			self._rPr[name] = val
		
	def vertAlign(self, attrs):
		vA = attrs['w:val']
		if vA == 'superscript':
			vA = 'super'
		elif vA == 'subscript':
			vA = 'sub'
		self.setStyle(vA, True)

	def tab(self, attrs):
		pass
		#self.pText += '\t'
	
	def br(self, attrs):
		self.pText += '\\\\\n'
	
	def pStyle(self, attrs):
		self._pPr['style'] = attrs['w:val']
	
	def ilvl(self, attrs):
		self._numPr['ilvl'] = int(attrs['w:val'])
	
	def numId(self, attrs):
		self._numPr['numId'] = int(attrs['w:val'])
	
	def noteReference(self, name, attrs):
		if self.options[name+'s'] is False:
			return
		text = '??'
		id = int(attrs['w:id'])
		try:
			text = self.references[name][id]
			logging.debug('%s %d = "%s"', name, id, text)
		except Exception as ex:
			logging.error('%s %d not in %s?', name, id, self.references[name])
			logging.exception(ex)
		if name == 'comment':
			self.pText += '%%\n\\startcomment[reference=c:%d]%%\n%s\n\\stopcomment%%\n' % (id, text)
		else:
			self.pText += '\\footnote[%s:%d]{%s}' % (name[0], id, text)

	def a_graphic(self, attrs):
		self.image = {'filename':''} # new image

	def a_blip(self, attrs):
		id = attrs['r:embed']
		self.image['id'] = id
		if id in self.links:
			fn = self.links[id].replace('media/','')
			logging.debug('image reference found: %s = %s', id, fn)
			self.image['filename'] = fn

	def pic_cNvPr(self, attrs):
		for key in attrs.keys():
			self.image[key] = attrs[key]

	def a_graphic_end(self):
		if not self.options['images']:
			return
		self.text += '''
		\\startplacefigure[location=here,reference=%(name)s,title={%(descr)s}]%% %(id)s
		\\externalfigure[%(filename)s]
		\\stopplacefigure\n''' % self.image

	def tbl(self, attrs):
		self.text += '\\bTABLE[split=yes]\n'

	def tbl_end(self):
		self.text += '\\eTABLE\n'

	def tr(self, attrs):
		self.text += '\\bTR'

	def tr_end(self):
		self.text += '\\eTR\n'

	def tc(self, attrs):
		self.text += '\n\\bTD '

	def tc_end(self):
		self.text += '\\eTD'

	def endElement(self, name):
		self.elcount[name] -= 1
		del self.elhier[-1]
		tag = name.replace('w:', '').replace(':', '_')
		if tag in ('footnote', 'endnote', 'comment'):
			if self.options[tag+'s'] is False:
				return
			logging.debug('registering %s in %s = "%s"', tag, self.references[tag], self.pText)
			self.references[tag][-1] = self.pText
			self.inRef = ''
		tag += '_end'
		if hasattr(self, tag):
			getattr(self, tag)()
	
	def endDocument(self):
		while self.section > 0:
			# close all sections
			self.text += '\\stop%s\n' % SECTIONS[self.section]
			self.section -= 1
		self.text = self.header + self.text
		if self.options['template'] == 'empty':
			self.text += '\n\\stop%s\n' % self.doctype


class AuxReader(object):
	def __init__(self, zipf, docname):
		"""
		Auxiliary Reader used by DOCReader
		for processing footnotes, endnotes and comments.
		Also uses ContextHandler
		
		zipf (zipfile.ZipFile): open DOCX file object
		docname (str): file path within DOCX
		"""
		self.docname = docname
		self.zipf = zipf
		self.parser = make_parser()
		self.handler = ContextHandler()
		self.parser.setContentHandler(self.handler)
		
	def process(self):
		self.parser.parse(self.zipf.open(self.docname))
		return self.handler.references


class DOCReader(object):
	def __init__(self, docx, **options):
		"""
		Read a DOCX file and return the text content as string
		
		docx (str): file path
		options (dict):
		  images (bool): extract images? (True)
		  comments (bool): process comments? (True)
		  endnotes (bool): process endnotes? (True)
		  footnotes (bool): process footnotes? (True)
		  handler (xml.sax.handler.ContentHandler): handler object (ContextHandler)
		"""
		self.docxfile = docx
		if not 'handler' in options:
			options['handler'] = ContextHandler
		self.options = options
		self.data = {'links': []}  # save header, footer, document, links
		self.links = defaultdict(str)
		self.notes = defaultdict(str)
		self.meta = defaultdict(str)

		# read file
		self.zipf = zipfile.ZipFile(self.docxfile)
		self.filelist = self.zipf.namelist()

		self.parser = make_parser()
		self.handler = options['handler'](**options)
		self.parser.setContentHandler(self.handler)
		
	def process(self):
		doc_xml = 'word/document.xml'
		self.handler.metadata = self.process_metadata()
		self.handler.links = self.process_links()
		self.handler.references = self.process_notes()
		# get main text
		self.parser.parse(self.zipf.open(doc_xml))
		text = self.handler.text

		if self.options['images']:
			# extract images
			for fname in self.filelist:
				_, extension = os.path.splitext(fname)
				if extension in [".jpg", ".jpeg", ".png", ".bmp"]:
					dst_fname = os.path.join(self.options['imagedir'], os.path.basename(fname))
					with open(dst_fname, "wb") as dst_f:
						logging.info('Writing image file %s', dst_fname)
						dst_f.write(self.zipf.read(fname))
				else:
					logging.debug('Not an image file: %s', fname)
		self.zipf.close()
		return text.strip()

	def process_links(self):
		link_doc = 'word/_rels/document.xml.rels'
		if not link_doc in self.filelist:
			logging.warn('no links found')
			return self.links
		doc = self.zipf.read(link_doc)
		root = ET.fromstring(doc)
		nodes = [ node.attrib for node in root ]
		self.links = {node['Id']: node['Target'] for node in nodes}
		logging.debug(self.links)
		return self.links

	def process_notes(self):
		for name in ('footnote', 'endnote', 'comment'):
			aux_doc = 'word/%ss.xml' % name
			if not aux_doc in self.filelist or self.options[name+'s'] is False:
				logging.warn('no %ss', name)
				continue
			obj = AuxReader(self.zipf, aux_doc)
			temp = obj.process()
			self.notes[name] = temp[name]
		logging.debug(self.notes)
		return self.notes
		
	def process_metadata(self):
		meta_doc = 'docProps/core.xml'
		if not meta_doc in self.filelist:
			logging.warn('Metadata file not found!')
			return self.meta
		doc = self.zipf.read(meta_doc)
		root = ET.fromstring(doc)
		for node in root:
			ns, key = node.tag.split('}')
			self.meta[key] = node.text or ''
		logging.debug(self.meta)
		return self.meta

QUOTES = {
	# double and single quotes in different languages
	'de': '„“‚‘',
	'en': '“”‘’',
}

REPLACEMENTS = (
	('...', '…'),
	('--', '–'),
	('\'s', '’s'),
)

def smallcaps(matcho):
	return '%s\\scaps{%s}%s' % (matcho.group(1), matcho.group(2).lower(), matcho.group(3))

def postprocess(text, lang='en'):
	for t in REPLACEMENTS:
		text = text.replace(t[0], t[1])
	if lang in QUOTES:
		quotes = QUOTES[lang]
		text = re.sub(r'%s(.*?)%s' % (quotes[0], quotes[1]), r'\\quotation{\1}', text, flags=re.U|re.M)
		text = re.sub(r'%s(.*?)%s' % (quotes[2], quotes[3]), r'\\quote{\1}', text, flags=re.U|re.M)
	if lang == 'de':
		text = re.sub(r'(\d+)\.(\d\d\d)', r'\1\\,\2', text) # Tausenderpunkte entfernen
		text = re.sub(r'(\d+)-(\d+)', r'\1–\2', text) # "bis"
		text = re.sub(r'(\d+)\s*x\s*(\d+)', r'\1\\,\\times\\,\2', text) # Multiplikationskreuz
		text = re.sub(r'(St|Dr|Prof)\.\s*(\w+)', r'\1.\\,\2', text, flags=re.U) # St, Dr, Prof
		text = re.sub(r'(v|n)\.\s*(Chr\.)', r'\1.\\,\2', text, flags=re.U) # v./n. Chr.
	elif lang == 'en':
		text = re.sub(r'(\W)(BC|AD)(\W)', smallcaps, text) # AD/BC
	text = re.sub(r'[ \t]+', ' ', text)
	return text


def process_doc(docx, **options):
	logging.info('processing %s' % docx)
	if os.path.basename(docx).startswith('.'):
		logging.warn('Ignoring hidden file/dir %s', docx)
		return False
	if os.path.isdir(docx):
		logging.info('%s is a directory', docx)
		for entry in os.scandir(docx):
			if not entry.name.startswith('.') and entry.is_file():
				process_doc(entry.path, img_dir)
	elif os.path.isfile(docx):
		logging.info('processing %s', docx)
		obj = DOCReader(docx, **options)
		result = obj.process()
		lang = obj.meta['language'] or DEFAULT_LANGUAGE
		if not options['raw']:
			result = postprocess(result, lang)
		template = '%(TEXT)s'
		if options['template'] != 'empty':
			logging.info('processing template')
			with open(options['template'], 'r', encoding='utf-8') as tpl:
				template = ''.join(tpl.readlines())
			DATA = defaultdict(str)
			DATA.update(obj.meta)
			DATA['filename'] = os.path.basename(docx)
			DATA['TEXT'] = result
			DATA['volume'] = 0
			result = template % DATA
		# target file name is like source file name
		# TODO: configuration option
		targetfile = docx.lower().replace(' ', '_').replace('.docx', '.tex')
		# TODO: check if target exists and save copy
		with open(targetfile, 'w', encoding='utf-8-sig') as text:
			logging.info('writing %s', targetfile)
			text.write(result)
	else:
		logging.warn('%s is not a file or directory!', docx)
	return True


@begin.start(auto_convert=True)
@begin.logging
def main(
	template: 'TeX template file (without .tex)' = 'empty', # TODO
	templatedir: 'Directory for templates' = './tpl',
	images: 'Extract embedded images?' = True,
	imagedir: 'Directory for extracted images' = './img',
	fonts: 'Include font switches?' = True,
	colors: 'Include color settings?' = True,
	footnotes: 'Include footnotes?' = True,
	endnotes: 'Include endnotes?' = True,
	comments: 'Include comments?' = True,
	raw: 'Don\'t try to enhance markup?' = False,
	*docs: 'List of documents or directories to convert'):
	options = defaultdict(str)
	for key in 'template templatedir images imagedir fonts colors footnotes endnotes comments raw'.split():
		options[key] = locals()[key]
	if template != 'empty':
		if not os.path.isdir(templatedir):
			logging.info('creating template directory %s', templatedir)
			os.makedirs(templatedir)
		if not os.path.isfile(template):
			tplfile = os.path.join(templatedir, template+'.tex')
			if os.path.isfile(tplfile):
				template = tplfile
				options['template'] = tplfile
				logging.info('loading template %s', tplfile)
			else:
				logging.warn('Template %s is not a file. Continuing without template.', template)
	if not images:
		imagedir = None
	else:
		if not os.path.isdir(imagedir):
			logging.info('creating image directory %s', templatedir)
			os.makedirs(imagedir)
	options['imagedir'] = imagedir
	for doc in docs:
		process_doc(doc, **options)
