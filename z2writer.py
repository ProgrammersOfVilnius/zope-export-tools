"""
Knows how to write files and directories corresponding to Zope 2 objects.

Supports only a few object types (e.g. no DTML documents); ignores most
metadata.

Usage:

    write_object(ob, 'file_or_directory_name')

Tested with Zope 2.14 on Python 2.7.

Copyright (c) 2010 Marius Gedminas <marius@pov.lt>

Licenced under the Zope Public Licence (ZPL) version 2.1.  Find a copy
in your Zope 2 distribution (without which this script is useless).
"""

import os

from OFS.Folder import Folder
from OFS.Image import Image, File
from OFS.interfaces import IPropertyManager
from OFS.DTMLMethod import DTMLMethod
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from Products.PythonScripts.PythonScript import PythonScript


HIGHEST, HIGH, NORMAL, LOW, LOWEST = range(5)
writer_registry = []


def writer(class_=None, condition=None, priority=NORMAL):
    if condition is None:
        assert class_ is not None
        condition = lambda o: isinstance(o, class_)
    else:
        assert class_ is None
    def decorator(fn):
        writer_registry.append((priority, condition, fn))
        writer_registry.sort() # a bit wasteful to resort every time
        return fn
    return decorator


warned_about = set()

def warn(msg):
    if msg not in warned_about:
        print msg
        warned_about.add(msg)


def class_name(cls):
    return '%s.%s' % (cls.__module__, cls.__name__)


def write_object(ob, filename):
    for priority, condition, handler in writer_registry:
        if condition(ob):
            try:
                handler(ob, filename)
            except:
                warn("failed to write %s (%s)" % (filename, class_name(ob.__class__)))
                raise
            break
    else:
        warn("skipping %s (%s)" % (filename, class_name(ob.__class__)))
        return
    write_metadata(ob, filename)


def metadata_filename(filename, isdir=None):
    if isdir is None:
        isdir = os.path.isdir(filename)
    if isdir:
        return os.path.join(filename, '.z2meta', '__this__')
    else:
        return os.path.join(os.path.dirname(filename),
                            '.z2meta',
                            os.path.basename(filename))


def write_metadata(ob, filename):
    if not IPropertyManager.providedBy(ob):
        return
    filename = metadata_filename(filename)
    dirname = os.path.dirname(filename)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    f = file(filename, 'w')
    print >> f, '[properties]'
    for prop in sorted(ob.propertyMap(), key=lambda prop: prop['id']):
        key = '%s:%s' % (prop['id'], prop['type'])
        value = getattr(ob, prop['id'])
        # TODO: selection and multiple selection need some more love
        # (saving prop['select_variable'] too)
        if isinstance(value, unicode):
            value = value.encode('UTF-8')
        value = str(value).encode('string-escape')
        print >> f, '%s = %s' % (key, value)
    f.close()


@writer(Folder)
def write_folder(folder, dirname):
    os.mkdir(dirname)
    for name, item in folder.objectItems():
        write_object(item, os.path.join(dirname, name))


@writer(PythonScript)
def write_py(script, filename):
    f = file(filename, 'w')
    f.write(script.read())
    f.close()


@writer(ZopePageTemplate)
def write_pt(pt, filename):
    f = file(filename, 'w')
    data = pt.read().encode('UTF-8')
    f.write(data)
    if not data.endswith('\n'):
        f.write('\n')
    f.close()


@writer(Image, priority=HIGH)
def write_image(img, filename):
    f = file(filename, 'wb')
    data = img.data
    if isinstance(data, str):
        f.write(data)
    else:
        while data is not None:
            f.write(data.data)
            data = data.next
    f.close()


@writer(File, priority=HIGH)
def write_file(fileobj, filename):
    f = file(filename, 'wb')
    f.write(str(fileobj))
    f.close()


@writer(DTMLMethod)
def write_dtml(dtml, filename):
    f = file(filename, 'w')
    data = dtml.document_src()
    f.write(data)
    if not data.endswith('\n'):
        f.write('\n')
    f.close()

