from koert.gnucash.tools import open_gcf
from koert.gnucash.balance import get_opening_balance, get_balance_at
from time import mktime, strptime
import koert.verification.fin7scheme as scheme
import argparse
import sys

def parse_args():
	parser = argparse.ArgumentParser(description="Show the balance")
	parser.add_argument("gnucash_file")
	parser.add_argument("--date", type=parse_time, default=None)
	parser.add_argument("--account", type=str, default=":")
	return parser.parse_args()

def parse_time(s):
	return mktime(strptime(s, '%Y-%m-%d'))

def get_relevant_children(ac):
	todo = [ac]
	while(len(todo)>0):
		ac = todo.pop()
		if len(ac.children)<=10:
			todo.extend(ac.children.values())
		yield ac

def main():
	args = parse_args()
	gcf = open_gcf(args.gnucash_file, scheme)
	book = gcf.fields['books'].values()[0]
	opb = None
	if args.date==None:
		opb =  get_opening_balance(book, 
				book.ac_by_path(":Openingsbalansen"))
	else:
		opb = get_balance_at(book, args.date)
	acs = get_relevant_children(book.ac_by_path(args.account))
	for ac in acs:
		print "%65s %10s" % (ac.path, str(opb[ac]))

if __name__=="__main__":
	main() 
