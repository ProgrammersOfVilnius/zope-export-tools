#!/usr/bin/python
"""
Extracts the contents of a Zope 2 export file (*.zexp) into a tree of
directories.

Supports only a few object types (Folder, Page Template, Python script);
ignores most metadata.

Tested with Zope 2.12 and Python 2.5.

Copyright (c) 2010 Marius Gedminas <marius@pov.lt>

Licenced under the Zope Public Licence (ZPL) version 2.1.  Find a copy
in your Zope 2 distribution (without which this script is useless).
"""

import os
import sys
import optparse
import shutil

from ZODB.DB import DB
from ZODB.MappingStorage import MappingStorage
from OFS import XMLExportImport

import z2writer


importer_registry = {}


def importer(format):
    def decorator(fn):
        importer_registry[format] = fn
        return fn
    return decorator


@importer('xml')
def import_object_from_xml(where, fp):
    return XMLExportImport.importXML(where._p_jar, fp)


@importer('zexp')
def import_object_from_zexp(where, fp):
    return where._p_jar.importFile(fp)


def create_memory_storage():
    storage = MappingStorage()
    db = DB(storage)
    return db


def import_object(fp, format='zexp', where=None):
    conn = None
    if where is None:
        db = create_memory_storage()
        conn = db.open()
        where = conn.root()
    importer = importer_registry.get(format)
    if not importer:
        sys.exit('unknown export format: %s' % format)
    ob = importer(where, fp)
    return ob


def main():
    parser = optparse.OptionParser(usage='%prog [options] file.zexp|file.xml [output-directory]',
                                   description='unpacks a Zope 2 export file'
                                               ' to filesystem objects')
    parser.add_option('-f', action='store', dest='format', type='str',
                      help='input format (xml or zexp);'
                      ' default is autodetected from filename')
    parser.add_option('--overwrite', action='store_true',
                      help='overwrite output file/directory tree')
    opts, args = parser.parse_args()
    if args:
        what = args[0]
        try:
            where = args[1]
        except IndexError:
            where = os.path.splitext(what)[0]
    else:
        parser.print_help()
        sys.exit()
    format = opts.format
    if not format:
        if what.endswith('.xml'):
            format = 'xml'
        else:
            format = 'zexp'
    ob = import_object(file(what, 'rb'), format)
    if opts.overwrite and os.path.exists(where):
        shutil.rmtree(where)
    z2writer.write_object(ob, where)


if __name__ == '__main__':
    main()

