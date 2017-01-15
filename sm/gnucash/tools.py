from koert.gnucash.xmlformat import SaxHandler
import gzip
import os.path
import cPickle
import sys
from warnings import warn
from subprocess import Popen, PIPE

def open_gcf_in_git_repo(repopath, filepath, cachepath=None, scheme=None):
    from git import Repo
    
    repo = Repo(repopath)
    commit = repo.head.commit
    mtime = commit.authored_date
    f = commit.tree[filepath].data_stream

    result =  parse_gcf(f, mtime, cachepath=cachepath, scheme=scheme)

    f.read()

    return result

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

def get_commit_name():
	directory = os.path.dirname(__file__)
	p = Popen('git rev-parse HEAD',
			stdout=PIPE, shell=True, cwd=directory)
	outp, err = p.communicate()
	return outp

def load_cache(cachepath, mtime):
	if not os.path.exists(cachepath):
		return False
	# Do not use the cache if the gnucash file is newer
	if mtime >= os.path.getmtime(cachepath):
		return False
	with open(cachepath,"r") as f:
		current_commit_name = get_commit_name()
		try:
			cached_commit_name, gcf = cPickle.load(f)
			if cached_commit_name!=current_commit_name:
				return False
                        print "loaded cache %s" % cachepath
			return gcf
		except Exception as e:
			warn("Failed to load pickled cache of Gnucash file " \
					"'%s': %s" % (cachepath, repr(e)))
			return False

def update_cache(cachepath, gcf):
	if sys.getrecursionlimit()<2000:
		sys.setrecursionlimit(2000)
	with open(cachepath,"w") as f:
		try:
			cPickle.dump((get_commit_name(),gcf),f)
		except RuntimeError as e:
			warn("""Failed to dump a pickled version of the \
gnucash file "%s" due to the RuntimeError below.  If this is a stack \
overflow, you might want to increase the maximum recursion depth by \
sys.setrecursionlimit.""")
			raise e

def parse_gcf(f, mtime, scheme=None, parse=saxparse, cachepath=None):
	if cachepath!=None:
		result = load_cache(cachepath,mtime)
		if result!=False:
			return result
	handler = SaxHandler(scheme)
	parse(f, handler)
	result = handler.result
        update_cache(cachepath, result)
	return result

def open_gcf(filepath, scheme=None, parse=saxparse, cachepath=None):
        if cachepath==None:
            cachepath = cache_path(filepath)
        with open(filepath) as f:
            return parse_gcf(f,os.path.getmtime(filepath),
                    scheme=scheme, parse=parse, cachepath=cachepath)
