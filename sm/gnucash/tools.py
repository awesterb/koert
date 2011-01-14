from xml.sax import parse
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

