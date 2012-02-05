from koert.drank.boozedir import BoozeDir
from koert.drank.reporting import EventReport
from koert.format.table import Table, Header
from datetime import date, datetime
import sys
import os
import argparse

def parse_args():
	parser = argparse.ArgumentParser(description="Prints info on boozedir")
	parser.add_argument("booze_dir")
	parser.add_argument('-v','--verbose',
			help="be verbose",
			dest="verbose", action="store_true")
	subparsers = parser.add_subparsers()
	income_p = subparsers.add_parser("income",
			description="Print an income for the whole year")
	income_p.set_defaults(handler=Program.income)
	incomeps_p = subparsers.add_parser("income-periods",
			description="Print an income statement per period")
	incomeps_p.set_defaults(handler=Program.income_periods)
	return parser.parse_args()


class Program:
	def __init__(self):
		self.args = parse_args()
		self.set_bd()
		self.args.handler(self)

	def log(self, level, text, *args):
		if self.args.verbose >= level:
			print (text % args)

	def set_bd(self):
		self.log(1,"  loading Boozedir ...")
		n = datetime.now()
		self.bd = BoozeDir(self.args.booze_dir)
		d = datetime.now() - n
		self.log(1,"    done (%s s)", d.seconds + d.microseconds*10**-6)


	def income_periods(self):
		factors = self.bd.factordir.factors.values()
		# Sort factors by mililiters; which is a bit silly
		barf = self.bd.barformdir.total_factors
		deliv = self.bd.delivdir.total_factors
		rank = lambda f: -max(barf.get(f,0), deliv.get(f,0))
		factors.sort(key=rank)
	
		periods = self.bd.eventdir.periods
		t = Table([Header("#", lambda p: str(p.number)),
			   Header("start date", lambda p: str(p.start_date)),
			   Header("end date", lambda p: str(p.end_date)),
			   Header("#bf", lambda p: str(len(tuple(p.barforms)))),
			   Header("#dl", lambda p: str(len(tuple(p.delivs))))], 
			   periods)
		print "The periods are:"
		print ""
		print t.format()
		print ""
		print ""
		for p in periods:
			ft = p.ftallied
			fd = p.fdelivered
			fg = p.fdiff
			get_data_tuple = lambda f: (f, 
					ft.get(f,0), fd.get(f,0), fg.get(f,0)) 
			dt_not_trivial = lambda t: not (t[1]==t[2]==t[3]==0)
			rows = filter(dt_not_trivial,
					[get_data_tuple(f) for f in factors])
			t = Table([Header("factor", lambda d: d[0].handle),
				   Header("tallied", lambda d: str(d[1])),
				   Header("deliv", lambda d: str(d[2])),
				   Header("result", lambda d: str(d[2]-d[1])),
				   Header("diff", lambda d: "%.0f" % d[3])],
				   rows)
			print ""
			print ""
			print p
			print t.format()


	def income(self):
		factors = self.bd.factordir.factors.itervalues()
		barf = self.bd.barformdir.total_factors
		deliv = self.bd.delivdir.total_factors
		_format = "%30s %8s %8s %8s %5s"
		
		print _format % ("FACTOR", "GETURFT", 
				"GEKOCHT", "RESULTAAT", "%TRF")
		for f in factors:
			fb = barf.get(f,0)
			fd = deliv.get(f,0)
			perc = "--" 
			if fb:
				perc = "%.0f" % ((fd-fb)/fb*100,)
			print _format % (f.handle, fb, fd, fd-fb, perc)

if __name__=="__main__":
	Program()
