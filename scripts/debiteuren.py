#!/usr/bin/python
from koert.gnucash.tools import open_gcf
from koert.gnucash.balance import get_opening_balance, get_balance_at, get_flow
from koert.gnucash.export import get_user_balance, get_debitors
from time import mktime, strptime
import argparse
import sys

def parse_args():
    parser = argparse.ArgumentParser(
            description="Create emails for debitors")
    parser.add_argument("gnucash_file")
    parser.add_argument("--debitors_account", 
            default=":Activa:Vlottende activa:Debiteuren:Leden")
    parser.add_argument("--creditors_account",
            default=":Passiva:Crediteuren")
    parser.add_argument("--name")

    return parser.parse_args()

def main():
    args = parse_args()
    gcf = open_gcf(args.gnucash_file)
    book = gcf.fields['books'].values()[0]

    if args.name!=None:
        print get_user_balance(book, 
                args.creditors_account+":"+args.name, 
                args.debitors_account+":"+args.name)['mutations']
    else:
        print  get_debitors(book,
                args.creditors_account, args.debitors_account)
    

if __name__=="__main__":
    main() 
