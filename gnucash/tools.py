from koert.gnucash.xmlformat import SaxHandler
from koert.checks import core as checks
import gzip
import os.path
import pickle
import sys
import yaml
import io
from warnings import warn
from subprocess import Popen, PIPE
from git import Repo


def open_gcf_in_git_repo(repopath, filepath, cachepath=None, updatecache=True):

    repo = Repo(repopath)
    commit = repo.head.commit
    mtime = commit.authored_date
    f = io.BytesIO(commit.tree[filepath].data_stream.read())

    result = parse_gcf(f, mtime, cachepath=cachepath, updatecache=updatecache)

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


def saxparse(f, handler):
    from xml.sax import parse as saxparse
    saxparse(f, handler)


def lxmlparse(f, handler):
    from lxml.etree import parse as lxmlparse
    from lxml.sax import saxify
    etree = lxmlparse(f)
    saxify(etree, handler)


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
    with open(cachepath, "rb") as f:
        current_commit_name = get_commit_name()
        try:
            cached_commit_name, gcf = pickle.load(f)
            if cached_commit_name != current_commit_name:
                return False
            print("loaded cache %s" % cachepath)
            return gcf
        except Exception as e:
            warn("Failed to load pickled cache of Gnucash file "
                 "'%s': %s" % (cachepath, repr(e)))
            return False


def update_cache(cachepath, gcf):
    if sys.getrecursionlimit() < 4000:
        sys.setrecursionlimit(4000)
    with open(cachepath, "wb") as f:
        try:
            pickle.dump((get_commit_name(), gcf), f)
        except RuntimeError as e:
            warn("""Failed to dump a pickled version of the \
gnucash file "%s" due to the RuntimeError below.  If this is a stack \
overflow, you might want to increase the maximum recursion depth by \
sys.setrecursionlimit.""")
            raise e


def parse_gcf(f, mtime, parse=saxparse, cachepath=None, updatecache=True):
    if cachepath is not None:
        result = load_cache(cachepath, mtime)
        if result:
            return result
    handler = SaxHandler()
    parse(f, handler)
    result = handler.result
    result.mtime = mtime
    if cachepath is not None:
        if updatecache:
            update_cache(cachepath, result)
    return result


def open_gcf(filepath, parse=saxparse, cachepath=None, updatecache=True):
    if cachepath is None:
        cachepath = cache_path(filepath)
    with open(filepath) as f:
        return parse_gcf(f, os.path.getmtime(filepath),
                         parse=parse, cachepath=cachepath,
                         updatecache=updatecache)


def open_yaml(path):
    with open(path) as f:
        d = yaml.load(f)

    dirname = os.path.dirname(path)
    gcf_path = os.path.join(dirname, d['path'])
    cache_path = None
    if "cache" in d:
        cache_path = os.path.join(dirname, d['cache'])
    gcf = None
    if 'repo' in d:
        repo_path = os.path.join(dirname, d['repo'])
        gcf = open_gcf_in_git_repo(repo_path, d['path'], cachepath=cache_path,
                updatecache=False)
    else:
        gcf = open_gcf(gcf_path, cachepath=cache_path)
    if 'meta' in d:
        gcf.meta = d['meta']
        gcf.book.meta = gcf.meta
    if 'opening balance' in d:
        gcf.book.ac_by_path(d['opening balance']).is_opening_balance = True
    if 'census token' in d:
        gcf.book.apply_census_token(d['census token'])
    if 'checks' in d:
        if d['checks']:
            checks.mark_all(gcf.book)

    update_cache(cache_path, gcf)

    return gcf
