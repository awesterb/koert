from koert.gnucash.tools import open_gcf
from koert.gnucash.core import Softref
from time import mktime, strptime
from koert.verification.fin7scheme import scheme
import argparse
import sys


def parse_args():
	parser = argparse.ArgumentParser(description="Returns information"
			" needed to check the softrefs")
	parser.add_argument("gnucash_file")
	return parser.parse_args()

class Program:
	def __init__(self, args):
		self.args = args

	def main(self):
		self.gcf = open_gcf(self.args.gnucash_file, scheme)
		self.book = self.gcf.book
		for kind in Softref.kinds:
			self.print_by_kind(kind)
			print ""
			print ""

	def print_by_kind(self,kind):
		print " ___ %4s ___ " % kind
		print ""
		print "MISSING:"
		missing = self.book.missing_softrefs_by_kind[kind]
		if len(missing)==0:
			print "\tnone"
		for a,b in missing:
			print "\t%s--%s" % (a.number_str, b.number_str)
		print ""
		print "MINIMA:"
		minimums = self.book.minimum_softrefs_by_kind[kind]
		if len(minimums)==0:
			print "\tnone"
		for m in minimums:
			print "\t%s" % m.number_str
		print ""
		print "MAXIMA:"
		maximums = self.book.maximum_softrefs_by_kind[kind]
		if len(maximums)==0:
			print "\tnone"
		for m in maximums:
			print "\t%s" % m.number_str
			

if __name__=="__main__":
	Program(parse_args()).main()
