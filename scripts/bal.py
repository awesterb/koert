from koert.gnucash.tools import open_gcf
from koert.gnucash.balance import get_opening_balance, get_balance_at
from time import mktime, strptime
import koert.verification.fin7scheme as scheme
import sys

def main(argv):
	if not len(argv)>=1+2 and len(argv)<=1+3:
		print "please provide (1) a path to a gnucash file, " \
				"(2) a path to an account and" \
				" optionally (3) a date."
	path, acpath = argv[1:3]
	gcf = open_gcf(path, scheme)
	book = gcf.fields['books'].values()[0]
	opb = None
	if len(argv)==1+2:
		opb =  get_opening_balance(book, 
				book.ac_by_path(":Openingsbalansen"))
	else:
		t = mktime(strptime(argv[3], '%Y-%m-%d %H:%M:%S'))
		opb = get_balance_at(book, t)
	ac = book.ac_by_path(acpath)
	print "%65s %10s" % (acpath, str(opb[ac]))

if __name__=="__main__":
	main(sys.argv)
