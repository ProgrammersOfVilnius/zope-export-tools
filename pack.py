#!/usr/bin/python
"""
Builds a Zope 2 import/export file out of regular files and directories.

Supports only a few object types (no DTML documents/methods); ignores most
metadata.

Tested with Zope 2.9 on Python 2.4 and Zope 2.12 on Python 2.5.

Copyright (c) 2007-2010 Marius Gedminas <marius@pov.lt>

Licenced under the Zope Public Licence (ZPL) version 2.1.  Find a copy
in your Zope 2 distribution (without which this script is useless).
"""

import sys
import optparse

import transaction
from ZODB.DB import DB
from ZODB.MappingStorage import MappingStorage
from OFS import XMLExportImport

import z2loader


def create_memory_storage():
    storage = MappingStorage()
    db = DB(storage)
    return db


exporter_registry = {}


def exporter(format):
    def decorator(fn):
        exporter_registry[format] = fn
        return fn
    return decorator


@exporter('xml')
def export_object_to_xml(ob, fp):
    XMLExportImport.exportXML(ob._p_jar, ob._p_oid, fp)


@exporter('zexp')
def export_object_to_zexp(ob, fp):
    ob._p_jar.exportFile(ob._p_oid, fp)


def export_object(ob, fp, format='zexp'):
    conn = None
    if ob._p_jar is None:
        db = create_memory_storage()
        conn = db.open()
        conn.root()['stuff'] = ob
        transaction.commit()
    exporter = exporter_registry.get(format)
    if not exporter:
        sys.exit('unknown export format: %s' % format)
    exporter(ob, fp)
    if conn is not None:
        conn.close()


def main():
    parser = optparse.OptionParser(usage='%prog [options] file-or-directory',
                                   description='builds a Zope 2 import file'
                                               ' from filesystem objects')
    parser.add_option('-o', action='store', dest='output', type='str',
                      help='output filename')
    parser.add_option('-f', action='store', dest='format', type='str',
                      help='output format (xml or zexp);'
                      ' default is autodetected from output filename')
    opts, args = parser.parse_args()
    if args:
        what = args[0]
    else:
        parser.print_help()
        sys.exit()
    ob = z2loader.load_object(what)
    if ob is None:
        sys.exit('cannot load %s' % what)
    format = opts.format
    if opts.output != '-':
        where = file(opts.output, 'wb')
        if not format:
            if opts.output.endswith('.xml'):
                format = 'xml'
            else:
                format = 'zexp'
    else:
        where = sys.stdout
        if not format: format = 'xml'
    export_object(ob, where, format)


if __name__ == '__main__':
    main()
