from datetime import datetime
from koert.common.bintree import BinarySearchTree
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

	@property
	def book(self):
		return self.books.values()[0]


class Book(GcObj):
	def __init__(self, fields, scheme):
		GcObj.__init__(self, fields)
		self._root = None
		self._scheme = scheme
		self._set_account_refs()
		self._trs_by_num = None
		self._trs_by_softref = None
		self._softrefs_by_kind = None
		self._acs_by_softref_kind = None
		self._maximum_softrefs_by_kind = None
		self._minimum_softrefs_by_kind = None
		self._missing_softrefs_by_kind = None
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
	def softrefs_by_kind(self):
		if self._softrefs_by_kind == None:
			self._set_softrefs_by_kind()
		return self._softrefs_by_kind

	def _set_softrefs_by_kind(self):
		res = {}
		for kind in Softref.kinds:
			res[kind] = BinarySearchTree()
		for tr in self.transactions.itervalues():
			for sr in tr.softrefs:
				res[sr.kind].insert(sr)
		self._softrefs_by_kind = res

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
	
	@property
	def maximum_softrefs_by_kind(self):
		if self._maximum_softrefs_by_kind == None:
			self._set_3m_softrefs_by_kind()
		return self._maximum_softrefs_by_kind
	
	@property
	def minimum_softrefs_by_kind(self):
		if self._minimum_softrefs_by_kind == None:
			self._set_3m_softrefs_by_kind()
		return self._minimum_softrefs_by_kind
	
		
	@property
	def missing_softrefs_by_kind(self):
		if self._missing_softrefs_by_kind == None:
			self._set_3m_softrefs_by_kind()
		return self._missing_softrefs_by_kind

	def _set_3m_softrefs_by_kind(self):
		maximum = {}
		minimum = {}
		missing = {}
		for kind in Softref.kinds:
			maximum[kind],minimum[kind],missing[kind] = \
					self._smamsbk_by_kind(kind)
		self._maximum_softrefs_by_kind = maximum
		self._missing_softrefs_by_kind = missing
		self._minimum_softrefs_by_kind = minimum

	
	def _smamsbk_by_kind(self, kind):
		previous = None
		missing = []
		maximum = []
		minimum = []
		for sr in self.softrefs_by_kind[kind]:
			# For a description of L,J,M, see below.
			L,J,M = self._smamsbk_compare(previous, sr)
			assert(L) # softrefs_by_kind[kind] is ordered
			if M:
				missing.append((previous,sr))
			if J:
				minimum.append(sr)
				if previous!=None:
					maximum.append(previous)
			previous = sr
		if previous!=None:
			maximum.append(previous) # now:  previous is the last
		return (maximum,minimum,missing)

	# returns a pair (L,J,M), where 
	#   L  is a bool which indicates whether s1 <= s2  
	#   J  is a bool which indicates whether there's a 'jump' 
	#      between sr1 and sr2 like 
	#          rvp3.4.5 -> rvp3.5.1
	#   M  is a bool which indicates whether it's obvious there
	#      are some Softrefs between sr1 and sr2, 
	#      for instance in this case:
	#          rvp3.4.5    rvp3.5.7
	#      if L is False, M is None
	def _smamsbk_compare(self,sr1,sr2):
		if sr1==None:
			return (True, True, False)
		L,M = True,False # We'll see if we're wrong
		n1, n2 = sr1.number, sr2.number
		j=0   
		# j will become the smallest index 
		#  at which n1 and n2 differ or 
		# min(len(n1),len(n2)) if such index does not exist.
		while j<len(n1) and j<len(n2) and n1[j]==n2[j]:
			j+=1
		# We can now see if there is a jump:
		J = j+1 < len(n1)
		# There are three reasons M might be True; they follow below.
		# Along the way, we'll see if L happens to be False.
		#  (I)   n2[j+m] != 1 for some m>1
		for k in xrange(j+1,len(n2)):
			if n2[k]==1:
				continue
			M=True
			break
		#  (II)  n2[j] != 1 if j=min(len(n1),len(n2))
		if j==min(len(n1),len(n2)):
			if n2[j]!=1:
				M = True
			if len(n1)>len(n2):
				L = False
				M = None
			return (L, J, M)
		# (III) n1[j] 
		if n1[j] > n2[j]:
			L = False
			M = None
		elif n1[j]+1<n2[j]:
			M = True
		return (L,J,M)

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

	def get_descendants(self):
		todo = [self]
		while len(todo)>0:
			desc = todo.pop()
			todo.extend(desc.children.itervalues())
			yield desc

	def get_deep_mutations(self):
		for desc in self.get_descendants():
			for mut in desc.mutations:
				yield mut
	
	def get_deep_trs(self):
		trs = set()
		for mut in self.get_deep_mutations():
			trs.add(mut.transaction)
		return trs

	@property
	def nice_id(self):
		return self.path	

class Transaction(GcObj):
	def __init__(self, fields):
		GcObj.__init__(self, fields)
		self._softrefs = tuple(Softref.from_text(self.description))

	def __repr__(self):
		if self.num:
			return "tr"+self.num
		else:
			return "<tr %s %s>" % (self.date_posted,
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
		bits = number_str.split(".")
		good_bits = [bit for bit in bits if bit != ""]
		try:
			number = tuple(map(int,good_bits))
		except ValueError as e:
			raise ValueError("Could not parse %r as Softref: %s"
					% (token, e))
		yield cls(kind=kind, number=number)

	def __init__(self, kind, number):
		self._kind = kind.lower()
		self._number = number

	def __cmp__(self, other):
		if not isinstance(other, Softref):
			return NotImplemented
		if self.kind != other.kind:
			return NotImplemented
		# NB: Ordering on tuples in Python is lexicographic
		return cmp(self.number, other.number)

	def __eq__(self, other):
		if not isinstance(other, Softref):
			return False
		if self.kind!=other.kind:
			return False
		return self.number == other.number

	def __hash__(self):
		return hash((self.kind, self.number))

	@property
	def kind(self):
		return self._kind

	@property
	def number(self):
		return self._number

	@property
	def number_str(self):
		return '.'.join(map(str,self._number))
	
	def __repr__(self):
		return "<Softref %s>" % self.code

	@property
	def code(self):
		return self.kind + self.number_str
