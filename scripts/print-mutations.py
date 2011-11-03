from koert.gnucash.tools import open_gcf
from koert.gnucash.balance import get_opening_balance, get_balance_at
from time import mktime, strptime
from koert.verification.fin7scheme import scheme
import argparse
import sys

def parse_args():
	parser = argparse.ArgumentParser(description="Print mutation of a"\
			"specified account")
	parser.add_argument("gnucash_file")
	parser.add_argument("--account", type=str, default=":")
	return parser.parse_args()

def main():
	args = parse_args()
	gcf = open_gcf(args.gnucash_file, scheme)
	book = gcf.book
	ac = book.ac_by_path(args.account)
	for mut in ac.get_descendants_mutations():
		print repr(mut)

if __name__=="__main__":
	main() 
