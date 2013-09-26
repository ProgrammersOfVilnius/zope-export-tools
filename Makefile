python = python
scripts = bin/pack-zexp bin/unpack-zexp bin/render

all: $(scripts)

$(scripts): bin/buildout buildout.cfg setup.py
	bin/buildout
	touch -c $(scripts)

bin/buildout: python/bin/python bootstrap.py
	python/bin/python bootstrap.py

python/bin/python:
	virtualenv -p $(python) python

