class GcStruct(object):
	def __init__(self, fields):
		self.fields = fields


class GcObj(GcStruct):
	def __init__(self, fields):
		GcStruct.__init__(self, fields)

	@property 
	def id(self):
		return self.fields['id']


class File(GcStruct):
	def __init__(self, fields):
		GcStruct.__init__(self, fields)
	
	@property
	def books(self):
		return self.fields['books']


class Book(GcObj):
	def __init__(self, fields):
		GcObj.__init__(self, fields)
		self._root = None
		self._set_account_refs()
		self._trs_by_num = None

	def _set_account_refs(self):
		for ac in self.accounts.itervalues():
			self._handle_account(ac)
		if self.root==None:
			raise ValueError("book %s has no root account." % self)
		for tr in self.transactions.itervalues():
			self._handle_transaction(tr)

	def _handle_account(self, ac):
		if ac.parent_id==None:
			self._handle_root_ac(ac)
			return
		ac.parent = self.accounts[ac.parent_id]
		if ac.name in ac.parent.children:
			raise ValueError(("%s has two children"
					" named %s") % (ac.parent,
						ac.name))
		ac.parent.children[ac.name] = ac
		if not ac.commodity:
			raise ValueError("%s's commodity is not set, "
					"but it is not the root account" % ac)
		

	def _handle_transaction(self, tr):
		for sp in tr.splits.itervalues():
			self._handle_split(sp)

	def _handle_split(self, sp):
		sp._account = self.accounts[sp.account_id]
		sp.account.mutations.append(sp)

	def _handle_root_ac(self, ac):
		if ac.type!='ROOT':
			print ac.fields
			raise ValueError("%s has no parent, but is not "
					"of type ROOT" % ac)
		if self._root != None:
			raise ValueError("Two root-accounts found: "
					" %s and %s" % (self._root, ac))
		self._root = ac
	
	@property
	def root(self):
		return self._root

	@property
	def accounts(self):
		return self.fields['accounts']

	@property
	def transactions(self):
		return self.fields['transactions']

	@property
	def commodities(self):
		return self.fields['commodities']

	
	@property
	def trs_by_num(self):
		if self._trs_by_num == None:
			self._set_trs_by_num()
		return self._trs_by_num

	def _set_trs_by_num(self):
		res = {}
		for tr in self.transactions.itervalues():
			num = tr.num
			if num not in res:
				res[num] = ()
			res[num] += (tr,)
		self._trs_by_num = res
	
	def tr_by_num(self, num):
		trs = self.trs_by_num[num]
		if len(trs)!=1:
			raise ValueError("there are multiple transactions, "
					"%s, with the same number %s" %
					(trs, num))
		return trs[0]


class Account(GcObj):
	def __init__(self, fields):
		GcObj.__init__(self, fields)
		# the following are set by the Book
		self._parent = None 
		self._children = {}
		self._mutations = []

	def __repr__(self):
		return "<Account %s>" % self.nice_id

	@property
	def parent_id(self):
		return self.fields['parent']

	def get_parent(self):
		return self._parent
	def set_parent(self, value):
		self._parent = value
		self.fields['parent'] = value.id
	parent = property(get_parent, set_parent)

	@property
	def name(self):
		return self.fields['name']

	@property
	def type(self):
		return self.fields['type']
	
	@property
	def description(self):
		return self.fields['description']

	@property
	def code(self):
		return self.fields['code']

	@property
	def commodity(self):
		return self.fields['commodity']

	@property
	def commodity_scu(self):
		return self.fields['commodity-scu']

	@property
	def children(self):
		return self._children

	@property
	def mutations(self):
		return self._mutations

	@property
	def nice_id(self):
		if self.name:
			return repr(self.name)
		return self.id
	

class Transaction(GcObj):
	def __init__(self, fields):
		GcObj.__init__(self, fields)
	
	@property
	def splits(self):
		return self.fields['splits']
	
	@property
	def description(self):
		return self.fields['description']

	@property
	def num(self):
		return self.fields['num']

	@property
	def date_posted(self):
		return self.fields['date-posted']

	@property
	def date_entered(self):
		return self.fields['date-entered']

	@property
	def currency(self):
		return self.fields['currency']


class Split(GcObj):
	def __init__(self, fields):
		GcObj.__init__(self, fields)
		# set by Book
		self._account = None

	@property
	def account_id(self):
		return self.fields['account']

	def get_account(self):
		return self._account
	def set_account(self, value):
		self._account = value
		self.fields['account'] = value.id
	account = property(get_account, set_account)

	@property
	def memo(self):
		return self.fields['memo']

	@property
	def reconciled_state(self):
		return self.fields['reconciled-state']

	@property
	def quantity(self):
		return self.fields['quantity']

	@property
	def value(self):
		return self.fields['value']

class Commodity(GcStruct):
	def __init__(self, fields):
		GcStruct.__init__(self, fields)

	@property
	def id(self):
		return self.fields['id']


class TimeStamp(GcStruct):
	def __init__(self, fields):
		GcStruct.__init__(self, fields)
	
	@property
	def date(self):
		return self.fields['date']

	@property
	def ns(self):
		return self.fields['ns']
