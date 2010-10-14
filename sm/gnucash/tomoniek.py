import moniek.env
from moniek.accounting.entities import Entity, ecol, Amount

class Push(object):
	def __init__(self, gcf):
		self.gcid2mid = {}
		self.book = None
		self.gcf = gcf
		self.push_gcf()

	def push_gcf(self):
		if len(self.gcf.books)!=1:
			raise ValueError("to push to moniek, "
					"the gnucash file should "
					"contain precisely one book; "
					"not %s" % len(self.gcf.books))
		self.book = self.gcf.books.values()[0]
		self.push_book()

	def push_book(self):
		self.push_account(self.book.root)
		for tr in self.book.transactions.itervalues():
			self.push_transaction(tr)
		for cm in self.book.commodities.itervalues():
			self.push_commodity(cm)

	def push_account(self, ac):
		data = {}
		data["type"] = "ac"
		data["description"] = ac.description
		data["name"] = ac.name
		if ac.parent:
			data['parent'] = self.gcid2mid[ac.parent.id]
		data["xgc"] = {}
		data["xgc"]["id"] = ac.id
		data["xgc"]["code"] = ac.code
		data["xgc"]["commodity-scu"] = ac.commodity_scu
		data["xgc"]["type"] = ac.type
		if ac.commodity:
			data["xgc"]["commodity_id"] = ac.commodity.id
		self.push_entity(data, ac.id)
		for child in ac.children.itervalues():
			self.push_account(child)

	def push_transaction(self, tr):
		data = {}
		data['type'] = 'tx'
		data['description'] = tr.description
		data['xgc'] = {}
		data['xgc']['id'] = tr.id
		data['xgc']['num'] = tr.num
		data['xgc']['date-posted'] = tr.date_posted.date
		data['xgc']['date-entered'] = tr.date_entered.date
		if tr.currency:
			data['xgc']['currency_id'] = tr.currency.id
		self.push_entity(data, tr.id)
		for sp in tr.splits.itervalues():
			self.push_split(sp, tr)


	def push_split(self, sp, tr):
		data = {}
		data['type'] = 'mt'
		data['description'] = sp.memo
		data['account'] = self.gcid2mid[sp.account_id]
		am = Amount({})
		am[tr.currency.id] = sp.value
		data['value'] = am._data
		data['xgc'] = {}
		data['xgc']['id'] = sp.id
		data['xgc']['reconciled-state'] = sp.reconciled_state
		data['xgc']['quantity'] = str(sp.quantity)
		self.push_entity(data, sp.id)
	
	def push_commodity(self, cm):
		pass

	def find_previous_id(self, gcid):
		d = ecol.find_one({'xgc.id': gcid})
		if d == None:
			return None
		return d['_id']

	def push_entity(self, data, gcid):
		oldid = self.find_previous_id(gcid)
		if oldid != None:
			data['_id'] = oldid
		ent = Entity(data)
		assert(gcid not in self.gcid2mid)
		self.gcid2mid[gcid] = ent.id
		ent.save()
