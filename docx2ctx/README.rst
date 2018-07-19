DOCX to ConTeXt
===============

This is a converter from MS Word DOCX to ConTeXt TeX source.
It works directly on the XML sources within the DOCX container.

| fiëé visuëlle
| Henning Hraban Ramm
| https://www.fiee.net


License
-------
Choose MIT, BSD, GPL3 or LGPL at will.


Dependencies
------------

* Python 3.5+ with standard library


Features
--------

* Some metadata is extracted and setup in preamble, while you don't use
  a template.

* Text styles are mapped to structure commands, but ATM just a few English,
  German and French default styles are configured, this will probably evolve
  over time. A configuration per project would make sense.
  Also, a completely bold paragraph is regarded a section title.

  * e.g. ``\startchapter[title={...}] ... \stopchapter``
  * Find a list of default text styles in https://www.thedoctools.com/downloads/DocTools_List_Of_Built-in_Style_English_Danish_German_French.pdf
  * Text style names are preserved in comments to alleviate manual corrections.

* basic text formatting:

  * bold: ``\strong`` (``\setuphighlight[strong]`` is provided)
  * italic: ``\emph`` (``\setuphighlight[emph]`` is provided)
  * sub-/superscript: ``\low``/``\high``
  * underline: ``\underbar``
  * strikethrough: ``\overstrike``

* notes:

  * footnotes, endnotes: ``\footnote`` (reference starts with 'f' or 'e')
  * comments: ``\startcomment ... \stopcomment``
  * disable with ``--no-footnotes``, ``--no-endnotes``, ``--no-comments``

* enumerations: type (bullet/number) is ignored.

  * ``\start/stopitemize``, ``\start/stopitem``

* tables: using "natural tables"

  * ``\bTABLE \bTR \bTD ... \eTD \eTR \eTABLE``
  * No handling of table formats, cell spans etc.

* images: get extracted as files

  * ``\startplacefigure[...] \externalfigure[...] \stopplacefigure``
  * disable with ``--no-images``

* language switches:

  * Main language is taken from document metadata and setup as ``\mainlanguage[...]``.
  * Language switches within the document are marked as ``{\language[...] }``.
  * Often there are several text snippets (runs) with the same language.
    These get not (yet) concatenated.

* colors:

  * All used colors are declared in preamble, you probably need to fix them.
  * text color: ``\color[...]``
  * background color: ``\H...{}`` and ``\definehighlight[H...]``
    in preamble (fix yourself)
  * disable with ``--no-colors``

* fonts:

  * All fonts used in font switches are declared in preamble as
    ``\definefont[F...][...*default]``, you probably need to fix them.
  * disable with ``--no-fonts``


Usage
-----
List of options see ``python3 docx2ctx.py -h``


Disclaimer
----------
This is provided as-is, not more and not less. No warranties.

I don't claim that this fits your needs or that the code would be
anyhow sophisticated, but it works for me.

Since this is an important part of my business, I won't give free
support or write more documentation. Read the code and change it
after your needs. Suggestions and pull requests are welcome.
