#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ConTeXt project management

(c) 2009-2020 by Henning Hraban Ramm, fiëé visuëlle

"""
# after Perl predecessor from 2002
version = '%prog 2020-04-28'

import os
import re
import sys
import shutil
import logging
from pathlib import Path
from optparse import OptionParser

LOG_MAP = {
    'NONE': logging.FATAL,
    'ERROR': logging.ERROR,
    'WARN': logging.WARN,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG
}

levels = ('environment', 'project', 'product', 'component')
prefixes = ('env_', 'project_', 'prd_', 'c_')

reProject = re.compile(r'^\s*\\project\s+(?P<name>\w+)')
reEnvironment = re.compile(r'^\s*\\environment\s+(?P<name>\w+)')

errors = False


def change_parent(options, logger):
    """
    insert call for current level into parent level file,
    e.g. `\component c_myfile` into `prd_myprod.tex`.
    """
    original = open(options.parentfile, 'r')
    lines = original.readlines()
    original.close()
    shutil.copy(options.parentfile, options.parentfile.replace(options.texsuffix, options.baksuffix))
    newfile = open(options.parentfile, 'w')
    if options.this.startswith(prefixes[options.thislevel]):
        thisName = options.this
    else:
        thisName = '%s%s' % (prefixes[options.thislevel], options.this)
    component_directory = Path(options.component_directory).resolve()
    if component_directory != Path.cwd():
        thisName = component_directory / thisName
    reIncluded = re.compile(r'^s*\\%s\s+(%s)' % (options.mode, thisName))
    alreadyIncluded = False
    lc = -1 # line count
    for line in lines:
        lc += 1
        if lc < 20: # only check first few lines
            m = reEnvironment.match(line)
            if m and not options.environment:
                options.environment = m.group('name')
            m = reProject.match(line)
            if m and not options.project:
                options.project = m.group('name')
        m = reIncluded.match(line)
        if m:
            alreadyIncluded = True
            logger.info('Call for %s "%s" already found in %s file "%s"' % (options.mode, options.this, options.parent, options.parentfile))
        # insert before last line
        if not alreadyIncluded and ('\\stop%s' % levels[options.parentlevel] in line):
            logger.info('Inserting call for %s "%s" into %s file "%s"' % (options.mode, options.this, options.parent, options.parentfile))
            newfile.write('\t\\%s %s\n' % (options.mode, thisName))
        newfile.write(line)
    newfile.close()
    return options


def make_file(options, logger):
    """
    create new file for current level, using template if there is one
    """
    directory = Path(options.directory)
    component_directory = Path(options.component_directory)
    if options.mode == 'component' and component_directory != Path.cwd():
        directory = directory / component_directory
        logger.debug(directory) ### DEBUG
    newfilename = directory / ('%s%s%s' % (prefixes[options.thislevel], options.this, options.texsuffix))
    logger.info('Creating %s file "%s"' % (options.mode, newfilename))
    if not options.template:
        options.templatefile = options.mode + options.inisuffix
    else:
        options.templatefile = options.template
    if not os.path.isfile(options.templatefile):
        logger.info('Template file "%s" not found (will proceed without template)' % options.templatefile)
        lines = ()
    else:
        template = open(options.templatefile, 'r')
        lines = template.readlines()
        template.close()
    if os.path.isfile(newfilename):
        logger.info('File "%s" exists, saving backup' % newfilename)
        shutil.copy(newfilename, newfilename.replace(options.texsuffix, options.baksuffix))
    newfile = open(newfilename, 'w')
    newfile.write('\\start%s %s%s\n' % (options.mode, prefixes[options.thislevel], options.this))
    if options.mode=='project':
        newfile.write('\\environment %s%s\n' % (prefixes[0], options.environment))
    else:
        newfile.write('\\project %s%s\n' % (prefixes[1], options.project))
    if options.mode=='component':
        newfile.write('\\product %s%s\n\n' % (prefixes[2], options.product))
    for l in lines:
        newfile.write(l)
    newfile.write('\n\\stop%s\n' % (options.mode))
    newfile.close()


def main():
    global errors
    usage = "usage: %prog [options]\n(env > prj > prd > cmp)\nProvide all names without prefix and suffix!"
    parser = OptionParser(usage=usage, version=version, description=__doc__)
    parser.add_option('-m', '--mode', help='create which type of file?', choices=levels, metavar='FILETYPE', default='component')
    parser.add_option('-c', '--component', '--cmp', help='create component file', metavar='NAME')
    parser.add_option('-p', '--product', '--prd', help='create or set product file', metavar='NAME')
    parser.add_option('-j', '--project', '--prj', help='create or set project file', metavar='NAME')
    parser.add_option('-e', '--environment', '--env', help='create or set environment file', metavar='NAME')
    parser.add_option('-i', '--template', '--ini', metavar='FILENAME', help='use non-default initial template file')
    parser.add_option('-d', '--directory', '--dir', metavar='DIRNAME', help='project path', default=os.curdir)
    parser.add_option('-C', '--component_directory', '--cmpdir', metavar='DIRNAME', help='path for component files below project path', default=os.curdir)
    parser.add_option('-S', '--texsuffix', metavar='texsuffix', help='TeX suffix', default='.tex') # or .mkiv
    parser.add_option('-I', '--inisuffix', metavar='inisuffix', help='INI suffix', default='.ini')
    parser.add_option('-B', '--baksuffix', metavar='baksuffix', help='backup suffix', default='.bak.tex')
    parser.add_option('-L', '--loglevel', help='Log level', choices=list(LOG_MAP.keys()), default='INFO')

    (options, args) = parser.parse_args()

    #### setup logging

    logformat = '%(levelname)8s:\t%(message)s'

    if options.loglevel:
        loglevel = LOG_MAP[options.loglevel]
    else:
        loglevel = logging.INFO

    logging.basicConfig(level=loglevel, format=logformat)
    logger = logging.getLogger()

    try:
        import coloredlogs
        coloredlogs.install(level=loglevel, fmt=logformat)
        # see also coloredlogs.readthedocs.io
    except Exception as ex:
        logger.debug('Error in loading the Python module coloredlogs. No colorful log messages, doesn’t matter. Try "pip3 install coloredlogs".')

    logger.debug('Loglevel: %s', options.loglevel)

    ### project directory defined and available?
    project_directory = Path(options.directory).resolve()
    if not project_directory.is_dir():
        try:
            project_directory.mkdir(parents=True, exist_ok=True)
            logger.info('Creating directory "%s"' % options.directory)
        except Exception as e:
            errors = True
            logger.error(e)
            logger.error('Project path "%s" is not a directory and could not get created.' % options.directory)

    ### component_directory
    component_directory = Path(project_directory / Path(options.component_directory)).resolve()
    if not component_directory.is_dir():
        try:
            component_directory.mkdir(parents=True, exist_ok=True)
            logger.info('Creating directory "%s"' % component_directory)
        except Exception as e:
            errors = True
            logger.error(e)
            logger.error('Component path "%s" is not a directory and could not get created' % component_directory)

    ### if component name contains a slash, use only the last part
    if options.mode == 'component' and options.component and '/' in options.component:
        logger.warning('Directory delimiter in component name; use --component_directory instead!')
        options.component = options.component.split('/')[-1]

    ### check mode
    if options.mode=='component' and not options.component:
        for l in levels:
            if hasattr(options, l) and getattr(options, l):
                options.mode=l

    if not hasattr(options, options.mode):
        errors = True
        logger.error('No name given for %s' % options.mode)

    ### check if the parent level is defined and its file available
    for i in range(len(levels)):
        if options.mode == levels[i]:
            options.thislevel = i
            options.this = getattr(options, levels[i])
            options.thisfile = os.path.join(options.directory, "%s%s%s" % (prefixes[i], options.this, options.texsuffix))
            if i>0:
                options.parentlevel = i-1
                options.parent = getattr(options, levels[i-1])
                options.parentfile = "%s%s%s" % (prefixes[i-1], options.parent, options.texsuffix)
                if i==options.thislevel:
                    if not options.parent:
                        errors = True
                        logger.error('no %s given for %s' % (levels[i-1], levels[i]))
                    else:
                        if not os.path.isfile(options.parentfile):
                            options.parentfile = os.path.join(options.directory, options.parentfile)
                        if not os.path.isfile(options.parentfile):
                            errors = True
                            logger.error('file "%s" not found' % options.parentfile)
                            options.thislevel = options.parentlevel
                            options.mode = levels[i+1] #levels[options.mode]
                            make_file(options)


    ### stop on errors
    if errors:
        logger.debug("Options: %s", options)
        logger.debug("Arguments: %s", args)
        parser.error("Errors occurred. See --help for options")
        #sys.exit(1)

    if options.thislevel > 1:
        options = change_parent(options, logger)
    make_file(options, logger)


if __name__ == '__main__':
    main()
