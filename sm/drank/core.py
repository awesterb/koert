import datetime
from os import listdir, path as ospath
from decimal import Decimal
from rikf import open_rikf_ar
from warnings import warn

class Factor:
	def __init__(self, handle, name):
		self.handle = handle
		self.name = name
	
	@classmethod
	def from_line(cls, line):
		if len(line)<1:
			raise ValueError("factor line is too small")
		handle, name = line[0:2]
		return cls(handle=handle, name=name)

	def __repr__(self):
		return self.name

	def __hash__(self):
		return hash(self.handle)^hash(self.name)


class Product:
	def __init__(self, handle, name, factors):
		self.handle = handle
		self.name = name
		self.factors = factors
	
	@classmethod
	def from_line(cls, line, boozedir):
		if len(line)<1:
			raise ValueError("product line is too small")
		handle, name = line[0:2]
		factors = {}
		for i in xrange(3,len(line)):
			field = line[i].strip()
			if field=="":
				break
			comps = field.split(":")
			if(len(comps)!=2):
				raise ValueError("error in factor multiple's"
						" formatting")
			amount_str, factor_name = comps
			amount = int(amount_str)
			factor = boozedir.factordir[factor_name]
			if factor in factors:
				raise ValueError("factor occurs twice")
			factors[factor] = amount
		return cls(handle=handle, name=name, factors=Count(factors))

	def __repr__(self):
		return self.name

	def __hash__(self):
		return hash(self.handle)^hash(self.name)

class ObjDirErr(Exception):
	pass

class ProductDir:
	def __init__(self, path, boozedir):
		products = {}
		self.boozedir = boozedir
		self.path = path
		ar = open_rikf_ar(path)
		for line in ar:
			product = Product.from_line(line, self.boozedir)
			handle = product.handle
			if handle in products:
				raise ValueError("product name appears twice")
			products[handle]=product
		self.products = products

	def __repr__(self):
		return "Product Directory"

	def __getitem__(self, name):
		if name not in self.products:
			warn("Unknown product: %s" % name)
			raise ObjDirErr()
		return self.products[name]
	
	def __contains__(self, name):
		return name in self.products


class FactorDir:
	def __init__(self, path):
		factors = {}
		self.path = path
		ar = open_rikf_ar(path)
		for line in ar:
			factor = Factor.from_line(line)
			handle = factor.handle
			if handle in factors:
				raise ValueError("factor name appears twice")
			factors[handle]=factor
		self.factors = factors

	def __repr__(self):
		return "Factor Directory"

	def __getitem__(self, name):
		if name not in self.factors:
			warn("Unknown factor: %s" % name)
			raise ObjDirErr()
		return self.factors[name]
	
	def __contains__(self, name):
		return name in self.factors

class Count:
	def __init__(self, countlets):
		self.countlets = countlets
	
	zero = None
	
	def __getitem__(self, item):
		return self.countlets[item]

	def __repr__(self):
		return "\n".join(["%s x %s" % (amount, obj) for 
			obj, amount in self.countlets.iteritems()])

	@classmethod
	def from_array(cls, ar, objdir):
		countlets = {}
		for line in ar:
			try:
				obj, amount = cls.countlet_from_line(line, 
						objdir)
			except ObjDirErr:
				continue
			if obj in countlets:
				raise ValueError("obj appears twice")
			countlets[obj] = amount
		return cls(countlets=countlets)
	
	@classmethod
	def countlet_from_line(cls, line, objdir):
		if len(line)==0:
			raise ValueError("no product given")
		obj = objdir[line[0]]
		amount = None
		if len(line)==1:
			amount = 0
		else:
			amount_str = line[1].strip()
			amount = 0 if amount_str=="" else int(amount_str)
		return obj, amount

	def __add__(self, other):
		countlets = {}
		for a in (self, other):
			for obj in a.countlets.iterkeys():
				if obj not in countlets:
					countlets[obj] = 0
				countlets[obj] += a[obj]
		return Count(countlets=countlets)
	
	def __neg__(self):
		countlets = {}
		for obj in self.countlets.iterkeys():
			countlets[obj] = -self.countlets[obj]
		return Count(countlets)
	
	

Count.zero = Count(countlets={})

class BarForm:
	def __init__(self, event, counter, shift, sell_count, 
			startbal, endbal, number):
		self.event = event
		self.counter = counter
		self.shift = shift
		self.startbal = startbal
		self.endbal = endbal
		self.sell_count = sell_count
		self.number = number

	@classmethod
	def from_path(cls, path, number, boozedir):
		ar = open_rikf_ar(path)
		return cls.from_array(ar, number, boozedir)

	@classmethod
	def from_array(cls, ar, number, boozedir):
		if len(ar)==0 or len(ar[0])==0 or ar[0][0].lower()!="bar":
			raise ValueError("Missing 'bar' title")
		if len(ar)==1 or len(ar[1])<5:
			raise ValueError("Incomplete/missing header")
		# header:  date ; counter ; shift# ; startbal ; endbal
		header = ar[1]
		date_str = header[0].strip()
		if date_str=="":
			date = None
		else:
			year, month, day = map(int, date_str.split("-"))
			date = datetime.date(year, month, day)
		counter = header[1]
		shift_str = header[2].strip()
		shift = int(header[2]) if shift_str!="" else None
		startbal = Decimal(header[3])
		endbal = Decimal(header[4])
		sell_count = Count.from_array(ar[2:], boozedir.productdir)
		event = boozedir.eventdir[date]
		return cls(event=event, counter=counter, shift=shift,
				startbal=startbal, endbal=endbal,
				sell_count=sell_count, number=number)

	@property
	def date(self):
		return self.event.date


class BarFormDir:
	def __init__(self, path, boozedir):
		self.barforms = {}
		self.boozedir = boozedir
		self.path = path
		self._total_sold = None
		self._load_barforms()
	
	@property
	def total_sold(self):
		if self._total_sold==None:
			self._total_sold = sum([bf.sell_count 
				for bf in self.barforms.itervalues()],
				Count.zero)
		return self._total_sold
	
	def _load_barforms(self):
		self.barforms = {}
		for fn in listdir(self.path):
			if len(fn)==0:
				continue
			if fn[0]==".":
				continue
			comps = fn.split(".")
			if len(comps)>1 and (comps[-1][-1]=="~" 
					or comps[-1][-1]=="swp"):
				continue
			number = comps[0]
			path = ospath.join(self.path, fn)
			bf = BarForm.from_path(path, number, self.boozedir)
			if number in self.barforms:
				raise ValueError("double number")
			self.barforms[number] = bf
			bf.event.register_barform(bf)

class Event:
	def __init__(self, date):
		self.date = date
		self.barforms = {}
	
	def register_barform(self, barform):
		shift = barform.shift
		if shift in self.barforms:
			raise ValueError("shift already taken")
		self.barforms[shift] = barform
	
	@property
	def shifts(self):
		return tuple(self.barforms.iterkeys())


class EventDir:
	def __init__(self):
		self.events = {}
	
	def __getitem__(self, date):
		if date not in self.events:
			self.events[date] = Event(date)
		return self.events[date]


class BeertankCount:
	def __init__(self, date, start, end):
		self.date = date
		self.start = start
		self.end = end

class BoozeDir:
	def __init__(self, path):
		self.eventdir = EventDir()
		self.factordir = FactorDir(ospath.join(path,
			"factor_catalog.csv"))
		self.productdir = ProductDir(ospath.join(path, 
			"product_catalog.csv"), self)
		self.barformdir = BarFormDir(ospath.join(path,
			"barforms"), self)
