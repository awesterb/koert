from koert.gnucash.xmlformat import SaxHandler
import gzip

def open_pos_gzipped(filepath):
	f = None
	try:
		# Only after a byte is read,  is the check whether filepath 
		# points to a gzipped file performed.
		f = gzip.open(filepath)
		f.read(1)
		f.rewind()
	except IOError:
		# message should read: "Not a gzipped file"
		f = open(filepath)
	return f

def saxparse(f,handler):
	from xml.sax import parse as saxparse
	saxparse (f, handler)

def lxmlparse(f,handler):
	from lxml.etree import parse as lxmlparse
	from lxml.sax import saxify
	etree = lxmlparse(f)
	saxify(etree,handler)

def open_gcf(filepath, scheme, parse=saxparse):
	handler = SaxHandler(scheme)
	f = open_pos_gzipped(filepath)
	parse(f, handler)
	return handler.result
