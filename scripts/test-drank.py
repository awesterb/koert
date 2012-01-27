from koert.drank.boozedir import BoozeDir
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
	cms = bd.commoditydir.commodities.values()
	print ""
	print ' -  --   ---     Checking Pricelists     ---   --  - '
	print ""
	print "   found pricelists: %s" % ", ".join(map(str,pls))
	print ""
	print ""

	missing = {}
	for c in cms:
		if c.proper:
			continue
		pl = c.pricelist
		if pl not in missing:
			missing[pl]=[]
		missing[pl].append(c.product)
	if missing:
		print "__________________________________________"
		print "The following pricelist miss some products:"
		print ""
		for pl in missing:
			_cmp = lambda p,q: cmp(p.handle, q.handle)
			missing[pl].sort(cmp = _cmp)
			print "%s" % (pl,)
			print ""
			print ", ".join(map(str,missing[pl]))
			print ""
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
		print "event on %s (%s):" % (
				event.date.strftime("%a %Y-%m-%d") \
						if event.date else "?", 
				', '.join(tags))
		for line in EventReport(event, bd).generate():
			print "\t* "+line

def check_barforms(args, bd):
	print ""
	print ' -  --   ---     Checking Barforms     ---   --  - '
	print ""
	print ""
	barforms = bd.barformdir.barforms
	codes = barforms.keys()
	check_barforms_numbering(args, bd, barforms, codes)

def check_barforms_numbering(args, bd, barforms, codes):
	intcodes = map(int, barforms.keys())
	m = min(intcodes)
	M = max(intcodes)
	print "Codes range from %s to %s." % (m,M)
	if len(intcodes) == M+1 - m:
		print "No barforms seem to be missing."
		return
	print "Some barforms are missing:"
	print "\tOne expects %s barforms in total" % (M+1-m,)
	print "\tbut there are only %s barforms." % (len(intcodes),)
	print
	print "Indeed, the following codes are not present: "
	ics = set(intcodes)
	for i in xrange(m,M+1):
		if i not in ics:
			print "\t%s" % (str(i),)


TESTS = {
	"pricelists": check_pricelists,
	"events": check_events,
	"barforms": check_barforms,
	"no": lambda *args,**kwargs: 42
}



# finally: 
if __name__=="__main__":
	main()
