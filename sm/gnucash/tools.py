from koert.gnucash.xmlformat import SaxHandler
import gzip
import os.path
import cPickle
import sys
from warnings import warn

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

def cache_path(filepath):
	return filepath + ".pickled"

def search_for_cache(filepath):
	cp = cache_path(filepath)
	if not os.path.exists(cp):
		return False
	# Do not use the cache if the gnucash file is newer
	if os.path.getmtime(filepath) >= os.path.getmtime(cp):
		return False
	with open(cp,"r") as f:
		try:
			return cPickle.load(f)
		except Exception as e:
			warn("Failed to load pickled cache of Gnucash file " \
					"'%s': %s" % (filepath, repr(e)))
			return False

def update_cache(filepath, gcf):
	cp = cache_path(filepath)
	if sys.getrecursionlimit()<2000:
		sys.setrecursionlimit(2000)
	with open(cp,"w") as f:
		try:
			cPickle.dump(gcf,f)
		except RuntimeError as e:
			warn("""Failed to dump a pickled version of the \
gnucash file "%s" due to the RuntimeError below.  If this is a stack \
overflow, you might want to increase the maximum recursion depth by \
sys.setrecursionlimit.""")
			raise e

def open_gcf(filepath, scheme, parse=saxparse, mind_cache=True):
	if mind_cache:
		result = search_for_cache(filepath)
		if result!=False:
			return result
	handler = SaxHandler(scheme)
	f = open_pos_gzipped(filepath)
	parse(f, handler)
	result = handler.result
	if mind_cache:
		update_cache(filepath, result)
	return result
