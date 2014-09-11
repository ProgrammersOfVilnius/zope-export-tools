Tools for working with Zope 2 websites
======================================

The Zope 2 through-the-web story kind of rules, but it also sucks a lot.  This
toolset lets you fetch your Zope 2 objects (Python Scripts and Page Templates)
into the filesystem, use your everyday tools with them (text editors, version
control systems) and push them back.

This particular copy of the toolset is tailored for working on a couple of
PoV-managed website, and may not work well with other Zopes.  It depends
on what kind of object types you use.


Installing
----------

Build it in place::

  make


Exporting objects to the filesystem
-----------------------------------

Method 1: WebDAV/FTP.  Not documented here.

Method 2: create an export file from the ZMI, download it, run ::

  bin/unpack-zexp filename.zexp [outdir]

If outdir is omitted, you'll get filename without the extension.

Both ZEXP and XML formats are supported.


Previewing changes
------------------

After editing page templates/Python scripts on the file system, check if they
work by doing ::

  bin/render folder/subfolder [filename ...] [--o outdir]

If outdir is omitted, prints the results to stdout.


Packing a ZEXP
--------------

When you're done, pack the directory into a zexp, scp it to the server, put it
into the Zope 2 instance directory and import it via the ZMI.

Warning: do *not* import it in /temp_folder and then move it to root, it'll get
garbage collected and your website will break.


Roundtrip compatibility
-----------------------

The exporter **ignores many object types** such as UserFolder, SQL Method,
MailHost, DTML Document, DTML Method.  It probably **discards some of the
metadata**.

The packer uses heuristics to **guess object types** from content.  It may
guess wrong.

Experiments (unpack--pack--unpack) show that Page Templates end up without
trailing newlines.

Export--modify--import loses all ZODB undo history, obviously.


Supported object types
----------------------

Currently only these object types are supported:

* File
* Image
* Python Script
* Zope Page Template
* Folder


Author
------

Marius Gedminas <marius@pov.lt>
