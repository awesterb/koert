from koert.gnucash.tools import open_gcf
from koert.gnucash.diff import ShallowGcStructDiff, \
  GcStructDiff, DictDiff, EqDiff, InDiff
from koert.verification.fin7scheme import scheme
import os.path
import sys

def main():
	if len(sys.argv) != 3:
		print "Please provide (1) a path to the gnucash file" \
				" and (2) a path to another gnucash file" \
				" to compare it with."
		return

	cmd, path_a, path_b = sys.argv
	
	print "Comparing:"
	print " A. %s  with " % (path_a,)
	print " B. %s ;" % (path_b,)
	print ""
	if not os.path.exists(path_a):
		print "File A does not exist"
		return
	if not os.path.exists(path_b):
		print "File B does not exist"
		return

	print "Loading A...  this may take a while..."
	A = open_gcf(path_a, scheme)
	print "done."
	print "" 
	print "Loading B..."
	B = open_gcf(path_b, scheme)
	print "done."
	print ""

	print "Computing difference..."
	print "   '-x' means x is in A, but not B; it has been removed"
	print "   '+x' means x is in B, but not A; it has been added"
	print "   '~x' means x has been changed; the difference follows in ( )"
	print ""
	print GcStructDiff(A,B)
	print ""
	print "done."

if __name__=="__main__":
	main()

