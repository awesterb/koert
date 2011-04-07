from datetime import datetime
import re

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
	def __init__(self, fields, scheme):
		GcObj.__init__(self, fields)
		self._root = None
		self._scheme = scheme
		self._set_account_refs()
		self._trs_by_num = None
		self._trs_by_softref = None
		self._acs_by_softref_kind = None
		self._apply_scheme()

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
			self._handle_split(sp, tr)

	def _handle_split(self, sp, tr):
		sp._account = self.accounts[sp.account_id]
		sp._transaction = tr
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

	def _apply_scheme(self):
		todo = [self.root]
		while(len(todo)>0):
			ac = todo.pop()
			self._apply_scheme_ac(ac)
			todo.extend(ac.children.itervalues())
	
	def _apply_scheme_ac(self, ac):
		if ac.parent!=None and ac.parent._softref_kinds!=None:
			ac._softref_kinds = ac.parent._softref_kinds
			return
		if ac.path in self.scheme.softref_kinds_by_account_path:
			ac._softref_kinds = \
				self.scheme.softref_kinds_by_account_path[
					ac.path]

	@property
	def scheme(self):
		return self._scheme

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

	def ac_by_path(self, path):
		bits = path.split(":")
		ac = self.root
		for bit in bits:
			if not bit:
				continue
			try:
				ac = ac.children[bit]
			except KeyError:
				raise KeyError("%s has no child named %s" % (
					ac, bit))
		return ac

	@property
	def trs_by_softref(self):
		if self._trs_by_softref == None:
			self._set_trs_by_softref()
		return self._trs_by_softref

	def _set_trs_by_softref(self):
		res = {}
		for tr in self.transactions.itervalues():
			for sr in tr.softrefs:
				code = sr.code
				if code not in res:
					res[code] = []
				res[code].append(tr)
		self._trs_by_softref = res

	@property
	def acs_by_softref_kind(self):
		if self._acs_by_softref_kind == None:
			self._set_acs_by_softref_kind()
		return self._acs_by_softref_kind
	
	def _set_acs_by_softref_kind(self):
		res = {}
		for ac, kinds in self.scheme.softref_kinds_by_account_path\
				.iteritems():
			for kind in kinds:
				if kind not in res:
					res[kind]=[]
				res[kind].append(ac)
		self._acs_by_softref_kind = res


class Account(GcObj):
	def __init__(self, fields):
		GcObj.__init__(self, fields)
		self._path = None
		# the following are set by the Book
		self._parent = None 
		self._children = {}
		self._mutations = []	
		self._softref_kinds = None

	def __repr__(self):
		return "<ac%s>" % self.nice_id

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
	def path(self):
		if self._path==None:
			self._path = self._create_path()
		return self._path
	def _create_path(self):
		if self.parent==None:
			return ""
		return ":".join((self.parent.path, self.name))

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
		return self.path	

class Transaction(GcObj):
	def __init__(self, fields):
		GcObj.__init__(self, fields)
		self._softrefs = tuple(Softref.from_text(self.description))

	def __repr__(self):
		return "<tr%s %s %s>" % (self.num if self.num else "", 
				self.date_posted, 
				repr(self.description))

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

	@property
	def softrefs(self):
		return self._softrefs


class Split(GcObj):
	def __init__(self, fields):
		GcObj.__init__(self, fields)
		# set by Book
		self._account = None
		self._transaction = None

	def __repr__(self):
		return "<sp %s %s by tr%s>" % (self.value, 
				self.account.nice_id, 
				self.transaction.num)

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
	def transaction(self):
		return self._transaction

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

	def __repr__(self):
		return datetime.fromtimestamp(self.date).strftime("%Y-%m-%d")

	@property
	def date(self):
		return self.fields['date']

	@property
	def ns(self):
		return self.fields['ns']


class Softref:
	kinds = ["rvp", "btr", 
			"bk1", "bk2", "gk", "rk", "lp", "lp-", "kr", "kz",
			"bk1-", "bk2-", "gk-", "rk-", "kr-", "kz-",
			"vp", "f", "dc"]
	regexp = re.compile("(%s)([0-9.]+)" % '|'.join(kinds), re.IGNORECASE)
	
	@classmethod
	def from_text(cls, text):
		for token in text.split():
			for sr in cls.from_token(token):
				yield sr

	@classmethod
	def from_token(cls, token):
		m = cls.regexp.match(token)
		if m==None:
			return
		kind, number_str = m.group(1, 2)
		number = number_str.split(".")
		yield cls(kind=kind, number=number)

	def __init__(self, kind, number):
		self._kind = kind.lower()
		self._number = map(lambda x: x.lower(), number)

	@property
	def kind(self):
		return self._kind

	@property
	def number(self):
		return self._number
	
	def __repr__(self):
		return "<Softref %s>" % self.code

	@property
	def code(self):
		return self.kind + '.'.join(self._number)
