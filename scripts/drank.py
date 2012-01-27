from koert.drank.boozedir import BoozeDir
from koert.drank.reporting import EventReport
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
			description="Print an income statement")
	income_p.set_defaults(handler=Program.income)
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
