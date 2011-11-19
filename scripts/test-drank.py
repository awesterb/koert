from koert.drank.core import BoozeDir, Count
from koert.drank.reporting import EventReport
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

def check_events(args, bd):
	pls = bd.pricelistdir.pricelists.values()
	print ""
	print ' -  --   ---     Checking Events     ---   --  - '
	print ""
	print ""
	dates = bd.eventdir.events.keys()
	_cmp = lambda x,y: 1 if x==None else -1 if y==None else  cmp(x,y)
	dates.sort(cmp=_cmp)
	for date in dates:
		event = bd.eventdir.events[date]
		tags = set()
		if event.beertank_activity:
			tags.add("beertank")
		if event.btc!=None:
			tags.add("btc")
		if len(event.delivs)>0:
			tags.add("deliv")
		if len(event.shifts)>0:
			tags.add("barform")
		if len(event.invcounts)>0:
			tags.add("invcount")
		print "event on %s (%s):" % (event.date, ', '.join(tags))
		for line in EventReport(event, bd).generate():
			print "\t* "+line


TESTS = {
	"pricelists": check_pricelists,
	"events": check_events
}



# finally: 
if __name__=="__main__":
	main()
