from sarah.order import sort_by_successors

class Verifier(object):
	def __init__(self, gcf):
		self.gcf = gcf
	
	def verify(self, *facts):
		todo = list(facts) 
		facts = set()
		while len(todo)>0:
			fact = todo.pop()
			if fact in facts:
				continue
			facts.add(fact)
			for dep,strong in fact.deps:
				todo.append(dep)
		l = list(facts)
		del todo
		del facts
		l = list(sort_by_successors(l, 
			lambda fact: [dep[0] for dep in fact.deps]))
		l.reverse()
		verified = set()
		results = {}
		for fact in l:
			if not all([(not strong) or dep in verified 
				for dep,strong in fact.deps]):
				results[fact] = None
				continue
			result = fact.verlet(self)
			if result.ok:
				verified.add(fact)
			results[fact] = result
		return results
			

class Fact(object):
	def __init__(self, verlet, deps=(), descr=None):
		self.deps = tuple(deps)
		self.verlet = verlet
		if descr == None:
			descr = "Verified by %s; depends on %s" % (verlet,
					deps)
		self.descr = descr
	
	def __repr__(self):
		return "<Fact: %s>" % self.descr
	def __eq__(self, other):
		return (self.deps==other.deps and
				self.verlet==other.verlet)
	def __hash__(self):
		return hash(self.deps) ^ hash(self.verlet)

def fact(deps=(), descr=None):
	return lambda verlet: Fact(verlet, deps=deps, descr=descr)


class Verlet(object):
	def __init__(self, verifier):
		self.v = verifier
		self.issues = []
		self.ok = self.get_ok()
		if self.ok:
			self.on_ok()
	def __repr__(self):
		comps = []
		ok_str = "ok" if self.ok else "failed"
		comps.append(ok_str)
		issues_str = '; '.join(self.issues)
		if issues_str != "":
			comps.append(issues_str)
		return "%s" % ': '.join(comps)
	def get_ok(self):
		raise NotImplementedError()
	def on_ok(self):
		pass


@fact(descr="there is precisely one book")
class OneBook(Verlet):
	def get_ok(self):
		return len(self.v.gcf.books)==1
	def on_ok(self):
		self.v.book = self.v.gcf.books.values()[0]


@fact(descr="each transaction has a unique number", deps=((OneBook, True),))
class TrsHaveNum(Verlet):
	def get_ok(self):
		mult_nums = []
		for (num, trs) in self.v.book.trs_by_num.iteritems():
			if num==None or num=="":
				self.issues.append("the transactions %s "
						"have no number" % 
						(tuple(trs),))
				continue
			if len(trs) == 1:
				continue
			mult_nums.append(str(num))
		if len(mult_nums)>0:
			self.issues.append("the numbers %s have multiple " 
					"transactions" % (tuple(mult_nums),))
		return len(self.issues)==0


@fact(descr="each transaction number is a 3-digit decimal", 
		deps=((OneBook,True),))
class TrNumsAreRemco(Verlet):
	def get_ok(self):
		fails = []
		maxnum = 0
		for num in self.v.book.trs_by_num.iterkeys():
			if num==None or num=="":
				continue
			if (len(num)==3 and 
					all([d in "0123456789" for d in num])):
				inum = int(num)
				if inum > maxnum:
					maxnum = inum
				continue
			fails.append(num)
		self.v.max_tr_num = maxnum
		if len(fails)>0:
			self.issues.append("the numbers %s are not" % 
					(tuple(fails),))
		return len(self.issues)==0

@fact(descr="the transactions numbers are continuous",
		deps=((TrNumsAreRemco,False), ))
class TrNumsAreRemcoContinuous(Verlet):
	def get_ok(self):
		fails = []
		for inum in xrange(1,self.v.max_tr_num+1):
			num = "%03d" % inum
			if num not in self.v.book.trs_by_num:
				fails.append(num)
		if len(fails)>0:
			self.issues.append("the numbers %s have no transaction"
					% (tuple(fails),))
		return len(self.issues)==0
