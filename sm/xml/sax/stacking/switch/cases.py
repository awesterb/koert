from koert.xml.sax.stacking import SH 

class Base(object):
	def __init__(self, name, handler):
		self.name = name
		self.handler = handler


class List(Base):
	def __init__(self, name, handler):
		Base.__init__(self, name, handler)
	
	def apply_result(self, result, cr):
		cr[self.name].append(result)

	def init(self, cr):
		cr[self.name] = []
	
	def final(self, cr):
		pass


class Single(Base):
	def __init__(self, name, handler, mandatory=False):
		Base.__init__(self, name, handler)
		self.mandatory = mandatory
	
	def apply_result(self, result, cr):
		if self.name in cr:
			raise ValueError("%s has double values; " + 
					"they are %s and %s" % (self.name, 
						result, cr[self.name]))
		cr[self.name] = result

	def init(self, cr):
		pass

	def final(self, cr):
		if self.name not in cr:
			if self.mandatory:
				raise ValueError("The field %s is manditory, "
						"but hasn't been set" 
						% self.name)
				assert(self.name in cr)
			else:
				cr[self.name] = None


class Dict(Base):
	def __init__(self, name, handler, key):
		Base.__init__(self, name, handler)
		self.key = key

	def apply_result(self, result, cr):
		k = self.key(result)
		assert(k not in cr[self.name])
		cr[self.name][k] = result

	def init(self, cr):
		cr[self.name] = dict()

	def final(self, cr):
		pass


class No(Base):
	def __init__(self):
		Base.__init__(self, "n/a", SH)

	def apply_result(self, result, cr):
		pass

	def init(self, cr):
		pass

	def final(self, cr):
		pass
No = No()
