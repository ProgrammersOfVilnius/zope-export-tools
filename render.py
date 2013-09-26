#!/usr/bin/python
"""
Renders Zope 2 page templates loaded from regular files and directories.

Supports only a few object types (no DTML documents/methods); ignores most
metadata.

Tested with Zope 2.9 on Python 2.4 and Zope 2.12 on Python 2.5.

Copyright (c) 2007-2010 Marius Gedminas <marius@pov.lt>

Licenced under the Zope Public Licence (ZPL) version 2.1.  Find a copy
in your Zope 2 distribution (without which this script is useless).
"""

import os
import sys
import optparse
import shutil
from cStringIO import StringIO

try:
    # Zope 2.12
    from zope.publisher.skinnable import setDefaultSkin
except ImportError:
    # Zope 2.9
    from zope.app.publication.browser import setDefaultSkin
from ZPublisher.Response import Response
from ZPublisher.Publish import Request
from ZPublisher.mapply import mapply
from ZPublisher.BaseRequest import RequestContainer
from ZPublisher import HTTPResponse
from OFS.Application import Application

try:
    # Zope 2.12
    from zope.configuration import xmlconfig
except ImportError:
    # Zope 2.9
    xmlconfig = None

import z2loader


try:
    from os.path import relpath
except ImportError:
    # Python 2.5 and older

    def relpath(path, start=os.path.curdir):
        """Return a relative version of a path"""
        from os.path import abspath, commonprefix, join, curdir, sep, pardir

        if not path:
            raise ValueError("no path specified")

        start_list = abspath(start).split(sep)
        path_list = abspath(path).split(sep)

        # Work out how much of the filepath is shared by start and path.
        i = len(commonprefix([start_list, path_list]))

        rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
        if not rel_list:
            return curdir
        return join(*rel_list)


class FakeZopeSecurityPolicy:

    def validate(self, accessed, container, name, value, context,
                 roles=None, getattr=getattr, _noroles=None,
                 valid_aq_=('aq_parent','aq_inner', 'aq_explicit')):
        print "Yahoo?"
        return True

    def checkPermission(self, permission, object, context):
        print "Blaaargh?"
        return True


def configure():
    HTTPResponse.default_encoding = 'UTF-8'
    if xmlconfig is not None:
        xmlconfig.string('<include package="Products.Five" />')


def render_object(obj, path, where, append_html=True, output_root='',
                  raise_errors=False):
    path = path.strip('/')
    assert '..' not in path
    outputfile = os.path.join(where, path)
    outputdir = os.path.dirname(outputfile)
    environ = {'SERVER_NAME': 'localhost',
               'SERVER_PORT': '80'}
    stdin = StringIO()
    response = Response(stdout=sys.stdout, stderr=sys.stderr)
    request = Request(stdin, environ, response)
    if output_root:
        request['SERVER_URL'] = relpath(output_root, outputdir)
    setDefaultSkin(request)
    app = Application().__of__(RequestContainer(REQUEST=request))
    obj = obj.__of__(app)
    request.other['VirtualRootPhysicalPath'] = obj.getPhysicalPath()
    obj = obj.unrestrictedTraverse(path)
    if getattr(obj, 'index_html', None) is not None:
        obj = obj.index_html
    try:
        result = mapply(obj, request.args, request)
    except Exception, e:
        print >> sys.stderr, "cannot render %s: %s: %s" % (path, e.__class__.__name__, e)
        if raise_errors:
            raise
    else:
        # make sure we insert <base href="..." /> etc.
        response.setBody(result)
        result = response.body
        if isinstance(result, unicode):
            result = result.encode('UTF-8')
        if where == '-':
            print '<!-- %s -->' % path
            if response.getStatus() != 200:
                print response.getStatus(), response.errmsg
                location = response.getHeader('Location')
                if location:
                    print 'Location:', location
            print result
        else:
            if response.getStatus() != 200:
                location = response.getHeader('Location')
                if location:
                    result = '<!-- Location: %s -->\n%s' % (location, result)
                result = '<!-- %s %s -->\n%s' % (response.getStatus(),
                                                 response.errmsg, result)
            content_type = (response.getHeader('Content-Type') or '').split(';')[0]
            html_response = (content_type == 'text/html')
            if not outputfile.endswith('.html') and html_response and append_html:
                outputfile += '.html'
            if not os.path.isdir(outputdir):
                os.makedirs(outputdir)
            print >> file(outputfile, 'w'), result


def render_folder(root, path, where,
                  object_types=['Page Template', 'File', 'Image'],
                  folder_types=['Folder'],
                  output_root=None,
                  raise_errors=False):
    path = path.strip('/')
    assert '..' not in path
    outputdir = os.path.join(where, path)
    os.makedirs(outputdir)
    if output_root is None:
        output_root = where
    app = Application()
    obj = root.__of__(app)
    folder = obj.unrestrictedTraverse(path)
    names = folder.objectIds(object_types)
    if 'index_html' not in names:
        names.append('index_html')
    for name in names:
        render_object(root, path + '/' + name, where,
                      append_html=False, output_root=output_root,
                      raise_errors=raise_errors)
    os.symlink('index_html', os.path.join(outputdir, 'index.html'))

    names = folder.objectIds(folder_types)
    for name in names:
        render_folder(root, path + '/' + name,
                      where,
                      object_types=object_types,
                      folder_types=folder_types,
                      output_root=output_root,
                      raise_errors=raise_errors)


def serve_folder(dir):
    from BaseHTTPServer import HTTPServer
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    os.chdir(dir)
    print "Serving http://localhost:8000/ ..."
    httpd = HTTPServer(('', 8000), SimpleHTTPRequestHandler)
    httpd.serve_forever()


def main():
    parser = optparse.OptionParser(usage='%prog [options] directory [object ...]',
                                   description='renders Zope 2 page templates'
                                               ' from filesystem objects')
    parser.add_option('-o', action='store', dest='output', type='str',
                      help='output location', default='-')
    parser.add_option('--overwrite', action='store_true',
                      help='overwrite output directory tree?')
    parser.add_option('--debug', action='store_true',
                      help='debug errors (show tracebacks)')
    parser.add_option('--pdb', action='store_true',
                      help='spawn pdb on errors')
    parser.add_option('--serve', action='store_true',
                      help='serve the results over http')
    opts, args = parser.parse_args()
    if len(args) < 1:
        parser.print_help()
        sys.exit()
    what = args.pop(0)
    ob = z2loader.load_object(what)
    if ob is None:
        sys.exit('cannot load %s' % what)
    if opts.pdb:
        opts.debug = True
    try:
        configure()
        if not args and opts.output == '-':
            args = ob.objectIds('Page Template')
        if args:
            for what in args:
                render_object(ob, what, opts.output,
                              raise_errors=opts.debug)
        else:
            if opts.overwrite and os.path.exists(opts.output):
                shutil.rmtree(opts.output)
            render_folder(ob, '', opts.output,
                          raise_errors=opts.debug)
            if opts.serve:
                serve_folder(opts.output)
    except KeyboardInterrupt:
        print
    except Exception, e:
        if opts.pdb:
            print "%s: %s" % (e.__class__.__name__, e)
            import pdb; pdb.post_mortem(sys.exc_info()[-1])
        else:
            raise


if __name__ == '__main__':
    main()
