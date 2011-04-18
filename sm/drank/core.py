import datetime
from os import listdir, path as ospath
from decimal import Decimal
from rikf import open_rikf_ar
from warnings import warn


def parse_date(date_str):
	if date_str=="":
		date = None
	else:
		year, month, day = map(int, date_str.split("-"))
		date = datetime.date(year, month, day)
	return date

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

# We often ignore the following errors
class MildErr(Exception):
	pass

# raised when, e.g., product does not appear in productdir.
class ObjDirErr(MildErr):
	pass

# raised when the string representation of a countlet
# has a white object name.
class NoObjStrErr(MildErr):
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
		return "\n".join(["%s: %s" % (obj, amount) for 
			obj, amount in self.countlets.iteritems()])

	@classmethod
	def from_array(cls, ar, objdir):
		countlets = {}
		for line in ar:
			if len(line)==0:
				continue
			try:
				obj, amount = cls.countlet_from_line(line, 
						objdir)
			except ObjDirErr:
				continue
			except NoObjStrErr:
				continue
			if obj in countlets:
				raise MildErr("obj appears twice: '%s'"
						"(amount: %s)"
						% (obj, amount))
			countlets[obj] = amount
		return cls(countlets=countlets)
	
	@classmethod
	def countlet_from_line(cls, line, objdir):
		if len(line)==0:
			raise ValueError("no object given")
		obj_str = line[0].strip()
		if(obj_str==""):
			raise NoObjStrErr()
		obj = objdir[line[0]]
		amount = None
		if len(line)==1:
			amount = 0
		else:
			amount_str = line[1].strip()
			try:
				amount = 0 if amount_str=="" \
						else int(amount_str)
			except ValueError:
				raise MildErr("could not parse amount: '%s'" \
						% amount_str)
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
			startbal, endbal, number, pricelist):
		self.event = event
		self.counter = counter
		self.shift = shift
		self.startbal = startbal
		self.endbal = endbal
		self.sell_count = sell_count
		self.number = number
		self.pricelist = pricelist

	@classmethod
	def from_path(cls, path, number, boozedir):
		ar = open_rikf_ar(path)
		return cls.from_array(ar, number, boozedir)

	@classmethod
	def from_array(cls, ar, number, boozedir):
		if len(ar)==0 or len(ar[0])==0 or ar[0][0].lower()!="bar":
			raise ValueError("Missing 'bar' title")
		if len(ar)==1 or len(ar[1])<6:
			raise ValueError("Incomplete/missing header")
		# header:
		#   pricelist; date ; counter ; shift# ; startbal ; endbal
		header = ar[1]
		pricelist_str = header[0].strip()
		pricelist = boozedir.pricelistdir[pricelist_str]
		date = parse_date(header[1].strip())
		counter = header[2]
		shift_str = header[3].strip()
		shift = int(header[3]) if shift_str!="" else None
		startbal = Decimal(header[4])
		endbal = Decimal(header[5])
		# below, to translate "product@pricelist" to a commodity
		commodity_view = boozedir.commoditydir.get_view(pricelist)
		sell_count = Count.from_array(ar[2:], commodity_view)
		event = boozedir.eventdir[date]
		return cls(event=event, counter=counter, shift=shift,
				startbal=startbal, endbal=endbal,
				sell_count=sell_count, number=number,
				pricelist=pricelist)

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
			comps, ignore = BoozeDir.processFn(fn)
			if ignore:
				continue
			try:
				bf = self._load_barform(fn, comps)
				bf.event.register_barform(bf)
			except MildErr as me:
				warn(("failed to load barform '%s': %s") \
						% (fn, me))
			self.barforms[bf.number] = bf

	def _load_barform(self, fn, comps):
		number = comps[0]
		path = ospath.join(self.path, fn)
		if number in self.barforms:
			raise ValueError("double number")
		return BarForm.from_path(path, number, self.boozedir)

class Event:
	def __init__(self, date):
		self.date = date
		self.barforms = {}
		self.btc = None

	def __str__(self):
		return "@"+("unspecified-time"
				if self.date==None else str(self.date))
	
	def register_barform(self, barform):
		shift = barform.shift
		if shift in self.barforms:
			raise MildErr("shift already taken: %s at %s" 
					% (shift, self.date))
		self.barforms[shift] = barform

	def register_btc(self, btc):
		if self.btc != None:
			raise MildErr("double registration")
		self.btc= btc

	
	@property
	def shifts(self):
		return tuple(self.barforms.iterkeys())


class EventDir:
	def __init__(self):
		self.events = {}
	
	def __getitem__(self, date):
		if isinstance(date,str):
			date = parse_date(date)
		if not isinstance(date,datetime.date) and date!=None:
			raise ValueError("date not a datetime, str or None:"
					" %s" %	repr(date))
		if date not in self.events:
			self.events[date] = Event(date)
		return self.events[date]

	# btc = beertankcount
	@classmethod
	def _load_btc_from_path(cls, path, boozedir):
		return cls._load_btc_from_array(open_rikf_ar(path), boozedir)

	@classmethod
	def _load_btc_from_array(cls, ar, boozedir):
		if len(ar)==0 or len(ar[0])==0 or ar[0][0].lower()!="tap":
			raise MildErr("beertankcount.csv has faulty header")
		count = Count.from_array(ar[1:], boozedir.eventdir)
		for event in count.countlets.iterkeys():
			event.register_btc(count[event])
		return count



class PriceList:
	def __init__(self, name, prices):
		self.prices = prices
		self.name = name
	
	@classmethod
	def from_path(cls, path, name, boozedir):
		ar = open_rikf_ar(path)
		return cls.from_array(ar, name, boozedir)

	@classmethod
	def from_array(cls, ar, name, boozedir):
		if len(ar)==0 or len(ar[0])==0 or \
				ar[0][0].lower()!="prijslijst":
			raise MildErr("Missing 'prijslijst' title")
		prices = Count.from_array(ar[1:], boozedir.productdir)
		return cls(name=name,prices=prices)

class PriceListDir:
	def __init__(self, path, boozedir):
		self.pricelists = {}
		self.boozedir = boozedir
		self.path = path
		self._load_pricelists()
	
	def _load_pricelists(self):
		for fn in listdir(self.path):
			comps, ignore = BoozeDir.processFn(fn)
			if ignore:
				continue
			try:
				bf = self._load_pricelist(fn, comps)
			except MildErr as me:
				warn("failed to load pricelist '%s': %s" \
						% (fn, me))
				continue
			self.pricelists[bf.name] = bf
	
	def _load_pricelist(self, fn, comps):
		path = ospath.join(self.path, fn)
		name = '.'.join(comps[0:-1])
		return PriceList.from_path(path, name, self.boozedir)

	
	def __getitem__(self, name):
		if name not in self.pricelists:
			warn("Unknown pricelist: %s" % name)
			raise ObjDirErr()
		return self.pricelists[name]

class Commodity:
	def __init__(self, product, pricelist):
		self.product = product
		self.pricelist = pricelist
	
	def __hash__(self):
		return hash(self.product) ^ hash(self.pricelist)


class CommodityDir:
	def __init__(self, boozedir):
		self.views = {}
		self.commodities = {}
		self.boozedir = boozedir

	def get_view(self, pricelist):
		if pricelist not in self.views:
			view = CommodityView(self, pricelist)
			self.views[pricelist] = view
		return self.views[pricelist]

	def get_commodity(self, product, pricelist):
		pair = (product, pricelist)
		if pair not in self.commodities:
			self.commodities[pair] = Commodity(*pair)
		return self.commodities[pair]

	def get_commodity_by_names(self, prod_name, pl_name):
		product = self.boozedir.productdir[prod_name]
		pricelist = self.boozedir.pricelistdir[pl_name]
		return self.get_commodity(product, pricelist)

class CommodityView:
	def __init__(self, comdir, pricelist):
		self.comdir = comdir
		self.pricelist = pricelist
	
	def __getitem__(self, name):
		t = name.split("@")
		if len(t) > 2:
			raise MildErr("commodity name '%s' has too many '@'s"
					% name)
		if len(t)==2:
			return self.comdir.get_commodity_by_names(*t)
		prod_name, = t
		product = self.comdir.boozedir.productdir[prod_name]
		return self.comdir.get_commodity(product, self.pricelist)


class BoozeDir:
	def __init__(self, path):
		self.eventdir = EventDir()
		self.beertankcount = \
				EventDir._load_btc_from_path(ospath.join(path,
			"beertankcount.csv"), self)
		self.factordir = FactorDir(ospath.join(path,
			"factor_catalog.csv"))
		self.productdir = ProductDir(ospath.join(path, 
			"product_catalog.csv"), self)
		self.pricelistdir = PriceListDir(ospath.join(path,
			"pricelists"), self)
		self.commoditydir = CommodityDir(self)
		self.barformdir = BarFormDir(ospath.join(path,
			"barforms"), self)

	@classmethod
	def processFn(cls, fn):
		comps = fn.split(".")
		if len(fn)==0:
			return comps, True
		if fn[0]==".":
			return comps, True
		if len(comps)>1:
			if comps[-1][-1]=="~" or comps[-1][-1]=="swp":
				return comps, True
			if comps[0]=='template':
				return comps, True
		return comps, False

