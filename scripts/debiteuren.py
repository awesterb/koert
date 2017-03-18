#!/usr/bin/env python
from koert.gnucash.tools import open_yaml
from koert.gnucash.export import get_user_balance, get_debitors
import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create emails for debitors")
    parser.add_argument("gnucash_file")
    parser.add_argument("--accounts",
            nargs="+",
            default=[ ":Activa:Vlottende activa:Debiteuren", 
                ":Passiva:Crediteuren"])
    parser.add_argument("--name")
    parser.add_argument("--alsonegative", action="store_true")
    parser.add_argument("--date", default=None)

    return parser.parse_args()


def main():
    args = parse_args()
    gcf = open_yaml(args.gnucash_file)
    book = gcf.book

    if args.name is not None:
        print(get_user_balance(book,
                               [args.creditors_account + ":" + args.name,
                                args.debitors_account
                                + ":" + args.name]))
    else:
        for name, value in get_debitors(book, args.accounts, day=args.date, onlypositive=(not args.alsonegative)):
            print("%30s %10s" % (name, value))


if __name__ == "__main__":
    main()
