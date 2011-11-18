from koert.drank.core import BoozeDir, Count
from datetime import date
import sys
import os
import argparse

TESTS=None

def parse_args():
	parser = argparse.ArgumentParser(description="Test booze directory")
	parser.add_argument("booze_dir")
	parser.add_argument("test", choices=TESTS.keys())
	return parser.parse_args()

def get_bd(args):
	return BoozeDir(args.booze_dir)

def main():
	args = parse_args()
	bd = get_bd(args)
	TESTS[args.test](args,bd)


# The tests

def check_pricelists(args, bd):
	pls = bd.pricelistdir.pricelists.values()
	print ""
	print ' -  --   ---     Checking Pricelists     ---   --  - '
	print ""
	print "   found pricelists: %s" % ", ".join(map(str,pls))
	print ""
	print ""

	unpriced = []
	for prod in bd.productdir.products.values():
		if [pl for pl in pls if (prod in pl.prices)]:
			continue
		unpriced.append(prod)
	if unpriced:
		print "____________________________________________________"
		print "The following products do not occur in any pricelist:"
		print ""
		print ", ".join(map(str,unpriced))
		print ""
		print ""



TESTS = {
	"check-pricelists": check_pricelists
}



# finally: 
if __name__=="__main__":
	main()
