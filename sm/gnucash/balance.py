from decimal import Decimal

def get_balance_at(book, date):
	trs = set()
	for tr in book.transactions.itervalues():
		if tr.date_posted.date<=date:
			trs.add(tr)
	return get_balance_from_trs(book, trs)

def get_opening_balance(book, obaccount):
	ob_muts = obaccount.mutations
	trs = [mut.transaction for mut in ob_muts]
	return get_balance_from_trs(book, trs)

def get_balance_from_trs(book, trs):
	muts = set()
	for tr in trs:
		muts.update(tr.splits.values())
	return get_balance_from_muts(book, muts)

def get_balance_from_muts(book, muts):
	balance = {}
	for ac in book.accounts.values():
		balance[ac] = Decimal(0)
	for mut in muts:
		ac = mut.account
		while ac!=None:
			balance[ac] += mut.value
			ac = ac.parent
	return balance

