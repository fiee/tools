#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ConTeXt project management

(c) 2009-2019 by Henning Hraban Ramm, fiëé visuëlle

"""
# after Perl predecessor from 2002
version = '%prog 2019-01-07'

import os
import re
import shutil
from optparse import OptionParser

levels = ('environment', 'project', 'product', 'component')
prefixes = ('env_', 'project_', 'prd_', 'c_')
TeXSuffix = '.tex'
IniSuffix = '.ini'
BackupSuffix = '.bak.tex'

reProject = re.compile(r'^\s*\\project\s+(?P<name>\w+)')
reEnvironment = re.compile(r'^\s*\\environment\s+(?P<name>\w+)')

def change_parent(options):
    """
    insert call for current level into parent level file,
    e.g. `\component c_myfile` into `prd_myprod.tex`.
    """
    original = open(options.parentfile, 'r')
    lines = original.readlines()
    original.close()
    shutil.copy(options.parentfile, options.parentfile.replace(TeXSuffix, BackupSuffix))
    newfile = open(options.parentfile, 'w')
    thisName = '%s%s' % (prefixes[options.thislevel], options.this)
    if options.component_directory != os.curdir:
        thisName = os.path.join(options.component_directory, thisName)
    reIncluded = re.compile(r'^s*\\%s\s+(%s)' % (options.mode, thisName))
    alreadyIncluded = False
    lc = -1
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
            print('Call for %s "%s" already found in %s file "%s"' % (options.mode, options.this, options.parent, options.parentfile))
        # insert before last line
        if not alreadyIncluded and ('\\stop%s' % levels[options.parentlevel] in line):
            print('Inserting call for %s "%s" into %s file "%s"' % (options.mode, options.this, options.parent, options.parentfile))
            newfile.write('\t\\%s %s\n' % (options.mode, thisName))
        newfile.write(line)
    newfile.close()
    return options

def make_file(options):
    """
    create new file for current level, using template if there is one
    """
    directory = options.directory
    if options.mode == 'component' and options.component_directory != os.curdir:
        directory = os.path.join(directory, options.component_directory)
    newfilename = os.path.join(directory, '%s%s%s' % (prefixes[options.thislevel], options.this, TeXSuffix))
    print('Creating %s file "%s"' % (options.mode, newfilename))
    if not options.template:
        options.templatefile = options.mode+IniSuffix
    else:
        options.templatefile = options.template
    if not os.path.isfile(options.templatefile):
        print('Template file "%s" not found (will proceed without template)' % options.templatefile)
        lines = ()
    else:
        template = open(options.templatefile, 'r')
        lines = template.readlines()
        template.close()
    if os.path.isfile(newfilename):
        print('File "%s" exists, saving backup' % newfilename)
        shutil.copy(newfilename, newfilename.replace(TeXSuffix, BackupSuffix))
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
    usage = "usage: %prog [options]\n(env > prj > prd > cmp)\nProvide all names without prefix and suffix!"
    parser = OptionParser(usage=usage, version=version, description=__doc__)
    parser.add_option('-m', '--mode', help='create which type of file?', metavar='FILETYPE', default='component')
    parser.add_option('-c', '--component', '--cmp', help='create component file', metavar='NAME')
    parser.add_option('-p', '--product', '--prd', help='create or set product file', metavar='NAME')
    parser.add_option('-j', '--project', '--prj', help='create or set project file', metavar='NAME')
    parser.add_option('-e', '--environment', '--env', help='create or set environment file', metavar='NAME')
    parser.add_option('-i', '--template', '--ini', metavar='FILENAME', help='use non-default initial template file')
    parser.add_option('-d', '--directory', '--dir', metavar='DIRNAME', help='project path', default=os.curdir)
    parser.add_option('-C', '--component_directory', '--cmpdir', metavar='DIRNAME', help='path for component files below project path', default=os.curdir)

    (options, args) = parser.parse_args()

    errors = []

    ### project directory defined and available?
    if not os.path.isdir(options.directory):
        try:
            os.makedirs(options.directory)
            print('create directory "%s"' % options.directory)
        except Exception as e:
            print(e)
            errors.append('project path "%s" is not a directory and could not get created' % options.directory)

    ### component_directory
    component_directory = os.path.join(options.directory, options.component_directory)
    if not os.path.isdir(component_directory):
        try:
            os.makedirs(component_directory)
            print('create directory "%s"' % component_directory)
        except Exception as e:
            print(e)
            errors.append('component path "%s" is not a directory and could not get created' % component_directory)

    ### if component name contains a slash, use only the last part
    if options.mode == 'component' and options.component and '/' in options.component:
        errors.append('directory delimiter in component name; use --component_directory instead!')
        options.component = options.component.split('/')[-1]

    ### check mode
    if options.mode=='component' and not options.component:
        for l in levels:
            if hasattr(options, l) and getattr(options, l):
                options.mode=l

    if not hasattr(options, options.mode):
        errors.append('no name given for %s' % options.mode)

    ### check if the parent level is defined and its file available
    for i in range(len(levels)):
        if options.mode == levels[i]:
            options.thislevel = i
            options.this = getattr(options, levels[i])
            options.thisfile = os.path.join(options.directory, "%s%s%s" % (prefixes[i], options.this, TeXSuffix))
            if i>0:
                options.parentlevel = i-1
                options.parent = getattr(options, levels[i-1])
                options.parentfile = "%s%s%s" % (prefixes[i-1], options.parent, TeXSuffix)
                if i==options.thislevel:
                    if not options.parent:
                        errors.append('no %s given for %s' % (levels[i-1], levels[i]))
                    else:
                        if not os.path.isfile(options.parentfile):
                            options.parentfile = os.path.join(options.directory, options.parentfile)
                        if not os.path.isfile(options.parentfile):
                            errors.append('file "%s" not found' % options.parentfile)
                            options.thislevel = options.parentlevel
                            options.mode = levels[i+1] #levels[options.mode]
                            make_file(options)


    ### stop on errors
    if errors:
        print(options, args)
        print("See --help for options")
        parser.error('\n\t'.join(errors))

    if options.thislevel > 1:
        options = change_parent(options)
    make_file(options)


if __name__ == '__main__':
    main()
