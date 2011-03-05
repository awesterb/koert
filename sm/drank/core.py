import datetime
from os import listdir, path as ospath
from decimal import Decimal
from rikf import open_rikf_ar

class Product:
	def __init__(self, handle, name):
		self.handle = handle
		self.name = name
	
	@classmethod
	def from_line(cls, line):
		if len(line)<1:
			raise ValueError("product line is too small")
		handle, name = line[0:2]
		return cls(handle=handle, name=name)

	def __repr__(self):
		return self.name

	def __hash__(self):
		return hash(self.handle)^hash(self.name)


class ProductCat:
	def __init__(self, path):
		products = {}
		self.path = path
		ar = open_rikf_ar(path)
		for line in ar:
			product = Product.from_line(line)
			handle = product.handle
			if handle in products:
				raise ValueError("product name appears twice")
			products[handle]=product
		self.products = products

	def __getitem__(self, name):
		return self.products[name]
	
	def __contains__(self, name):
		return name in self.products


class Count:
	def __init__(self, countlets):
		self.countlets = countlets
	
	zero = None
	
	def __getitem__(self, item):
		return self.countlets[item]

	def __repr__(self):
		return "\n".join(["%s x %s" % (amount, prod) for 
			prod, amount in self.countlets.iteritems()])

	@classmethod
	def from_array(cls, ar, proddir):
		countlets = {}
		for line in ar:
			product, amount = cls.countlet_from_line(line, proddir)
			if product in countlets:
				raise ValueError("product appears twice")
			countlets[product] = amount
		return cls(countlets=countlets)
	
	@classmethod
	def countlet_from_line(cls, line, proddir):
		if len(line)==0:
			raise ValueError("no product given")
		product = proddir[line[0]]
		amount = None
		if len(line)==1:
			amount = 0
		else:
			amount_str = line[1].strip()
			amount = 0 if amount_str=="" else int(amount_str)
		return product, amount

	def __add__(self, other):
		countlets = {}
		for a in (self, other):
			for prod in a.countlets.iterkeys():
				if prod not in countlets:
					countlets[prod] = 0
				countlets[prod] += a[prod]
		return Count(countlets=countlets)
	
	def __neg__(self):
		countlets = {}
		for prod in self.countlets.iterkeys():
			countlets[prod] = -self.countlets[prod]
		return Count(countlets)
	
	

Count.zero = Count(countlets={})

class BarForm:
	def __init__(self, date, counter, shift, sell_count, 
			startbal, endbal, number):
		self.date = date
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
		shift = header[2]
		startbal = Decimal(header[3])
		endbal = Decimal(header[4])
		sell_count = Count.from_array(ar[2:], boozedir.productdir)
		return cls(date=date, counter=counter, shift=shift,
				startbal=startbal, endbal=endbal,
				sell_count=sell_count, number=number)

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
			

class BeertankCount:
	def __init__(self, date, start, end):
		self.date = date
		self.start = start
		self.end = end

class BoozeDir:
	def __init__(self, path):
		self.productdir = ProductCat(ospath.join(path, 
			"product_catalog.csv"))
		self.barformdir = BarFormDir(ospath.join(path,
			"barforms"), self)
