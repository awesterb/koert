from decimal import Decimal

# Returns the transactions 
#       from    only this account (or its subaccounts) if specified
# in the period
#       begin   -ing at this date if provided and 
#       end     -ing at this date if provided.
#
# That is, if *begin* is not provided, the period has no begin, etc.
# So if *begin*, *end* and *from* are not specified,
# all transactions are returned.
def get_trs(book, _from=None, begin=None, end=None):
	trs = set()
	if not _from:
		_from = book.root
	for tr in _from.get_deep_trs():
		if not tr_in_period(tr, begin, end):
			continue
		trs.add(tr)
	return trs

# Given a set of transactions from *get_trs* specified by kwargs,
# returns the _flow_ to each account,
# which is the sum of the amounts of the mutations of this account.
def get_flow(book, **kwargs):
	return get_flow_from_trs(book, get_trs(book, **kwargs))

# Returns the balance of each account at a given date,
# which is the flow to that account upto the given date.
def get_balance_at(book, date):
	return get_flow(book, end=date)

# Returns the opening balance,
# which is the flow from the Equity account *obaccount*.
def get_opening_balance(book, obaccount):
	return get_flow(book, _from=obaccount)


################ INTERNALS ####################################################

def tr_in_period(tr, begin, end):
	if end and tr.date_posted.date > end:
		return False
	if begin and tr.date_posted.date < begin:
		return False
	return True


def get_flow_from_trs(book, trs):
	muts = set()
	for tr in trs:
		muts.update(tr.splits.values())
	return get_flow_from_muts(book, muts)

def get_flow_from_muts(book, muts):
	flow = {}
	for ac in book.accounts.values():
		flow[ac] = [Decimal(0), Decimal(0)]
	for mut in muts:
		ac = mut.account
		val = mut.value
		pos = (val >= 0)
		while ac!=None:
			if pos:
				flow[ac][0] += val
			else:
				flow[ac][1] += val
			ac = ac.parent
	return flow
