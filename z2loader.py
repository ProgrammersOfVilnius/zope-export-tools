"""
Knows how to load a Zope 2 website from regular files and directories.

Supports only a few object types (no DTML documents/methods); ignores most
metadata.

Usage:

    ob = load_object('file_or_directory_name')

Tested with Zope 2.9 on Python 2.4 and Zope 2.12 on Python 2.5.

Copyright (c) 2007-2010 Marius Gedminas <marius@pov.lt>

Licenced under the Zope Public Licence (ZPL) version 2.1.  Find a copy
in your Zope 2 distribution (without which this script is useless).
"""

import os

from OFS.Folder import Folder
from OFS.Image import Image, File
from OFS.interfaces import IPropertyManager
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from Products.PythonScripts.PythonScript import PythonScript


HIGHEST, HIGH, NORMAL, LOW, LOWEST = range(5)
loader_registry = []


def loader(condition, priority=NORMAL):
    def decorator(fn):
        loader_registry.append((priority, condition, fn))
        loader_registry.sort() # a bit wasteful to resort every time
        return fn
    return decorator


def load_object(filename):
    for priority, condition, handler in loader_registry:
        if condition(filename):
            obj = handler(filename)
            load_metadata(obj, filename)
            return obj
    print "skipping", filename
    return None


def metadata_filename(filename, isdir=None):
    if isdir is None:
        isdir = os.path.isdir(filename)
    if isdir:
        return os.path.join(filename, '.z2meta', '__this__')
    else:
        return os.path.join(os.path.dirname(filename),
                            '.z2meta',
                            os.path.basename(filename))


def load_metadata(ob, filename):
    if not IPropertyManager.providedBy(ob):
        return
    filename = metadata_filename(filename)
    if not os.path.exists(filename):
        return
    f = file(filename, 'r')
    for line in f:
        line = line.rstrip('\n')
        if line == '[properties]':
            break
    for line in f:
        line = line.rstrip('\n')
        if line.startswith('['):
            break
        if line.startswith('#'):
            continue
        if not line.strip():
            continue
        if ' = ' not in line:
            print "%s: bad metadata line: %s" % (filename, line)
            continue
        key, value = line.split(' = ', 1)
        if ':' not in key:
            print "%s: bad metadata key: %s" % (filename, key)
            continue
        name, type = key.split(':')
        value = value.decode('string-escape')
        # TODO: saner type conversion

        if type == 'boolean':
            if value in ('True', 'False'):
                value = (value == 'True')
            else:
                value = int(value)
        elif type == 'int':
            value = int(value)
        elif type == 'string':
            pass
        elif type == 'ustring':
            value = unicode(value, 'UTF-8')
        else:
            print "%s: unsupported type: %s" % (filename, type)
            continue

        # TODO: handle selection/multiple selection
        if not ob.hasProperty(name):
            ob.manage_addProperty(name, value, type)
            # XXX: apparently type == 'tokens' also needs special handling
        else:
            setattr(ob, name, value)
    f.close()


@loader(condition=os.path.isdir, priority=HIGHEST)
def load_folder(subdir):
    id = os.path.basename(subdir.rstrip(os.path.sep))
    f = Folder(id)
    for filename in os.listdir(subdir):
        if filename.startswith('.'):
            continue
        full_name = os.path.join(subdir, filename)
        obj = load_object(full_name)
        if obj is not None:
            f._setObject(filename, obj)
    return f


def detect_py(filename):
    first_line = file(filename).readline()
    return (filename.endswith('.py') or
            first_line.startswith("## Script (Python)"))


@loader(condition=detect_py)
def load_py(filename):
    id = os.path.basename(filename)
    ob = PythonScript(id)
    ob.write(file(filename).read())
    return ob


def detect_pt(filename):
    first_line = file(filename).readline().lstrip()
    return (filename.endswith('.pt')
            or first_line.startswith('<') and first_line[1:2].isalpha()
            or first_line.startswith('<!'))


@loader(condition=detect_pt)
def load_pt(filename):
    id = os.path.basename(filename)
    return ZopePageTemplate(id,
                            text=file(filename).read().decode('UTF-8'),
                            content_type='text/html')


def detect_image(filename):
    return (filename.endswith('.gif') or filename.endswith('.png') or
            filename.endswith('.jpg'))


@loader(condition=detect_image)
def load_image(filename):
    id = os.path.basename(filename)
    ob = Image(id, '', '')
    ob.update_data(file(filename, 'rb').read())
    return ob


@loader(condition=lambda filename: True, priority=LOWEST)
def load_file(filename):
    id = os.path.basename(filename)
    ob = File(id, '', '')
    ob.update_data(file(filename, 'rb').read())
    return ob
