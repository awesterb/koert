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

def get_balance_history(book, trs):
	date_trs = {}
	for tr in trs:
		d = tr.date_posted.date
		if d not in date_trs:
			date_trs[d] = []
		date_trs[d].append(tr)
	dates = list(date_trs.keys())
	dates.sort()
	balance = {}
	for ac in book.accounts.values():
		balance[ac] = Decimal(0)
	for date in dates:
		balance = dict(balance)
		for tr in date_trs[date]:
			for mut in tr.splits.values():
				ac = mut.account
				while ac!=None:
					balance[ac] += mut.value
					ac = ac.parent
		yield (date, balance)
			
