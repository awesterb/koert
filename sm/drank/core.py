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
			raise ValueError("product line is too small: '%s' " \
					% (line,))
		handle, name = line[0:2]
		factors = {}
		for i in xrange(2,len(line)):
			field = line[i].strip()
			if field=="":
				break
			comps = field.split(":")
			if(len(comps)!=2):
				raise ValueError("error in factor multiple's"
						" formatting; components: "
						" %s " % (comps,) + "; "
						"did you forget a colon?")
			amount_str, factor_name = comps
			amount = int(amount_str)
			factor = boozedir.factordir[factor_name]
			if factor in factors:
				raise ValueError("factor occurs twice")
			factors[factor] = amount
		if len(factors)==0:
			raise MildErr("product %s (%s) has no factors" 
					% (handle, name))
		return cls(handle=handle, name=name, 
				factors=Count(factors, int))

	def __repr__(self):
		return self.handle

	def __hash__(self):
		return hash(self.handle)^hash(self.name)

	@property
	def beertank(self):
		for f in self.factors:
			if f.handle == BoozeDir.btfactorhandle:
				return self.factors[f]
		return self.factors.constr(0)

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
			try:
				product = Product.from_line(line, self.boozedir)
			except MildErr:
				warn("Failed to load product from line: %s" 
						% (line,))
				continue
			handle = product.handle
			if handle in products:
				warn("product handle appears"
						"twice: %s" % handle)
				continue
			products[handle]=product
		self.products = products

	def __repr__(self):
		return "Product Directory"

	def __getitem__(self, name):
		if name not in self.products:
			warn("Unknown product: '%s'" % name)
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
				raise ValueError("factor handle appears "
					"twice: %s" % (handle,))
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
	def __init__(self, countlets, constr):
		self.countlets = countlets
		self.constr = constr
	
	@classmethod
	def zero(cls, constr):
		return Count({}, constr)
	
	def __getitem__(self, item):
		return self.countlets[item]

	def __contains__(self, item):
		return item in self.countlets

	def __iter__(self):
		return iter(self.countlets)

	def __repr__(self):
		return "\n".join(["%s: %s" % (obj, amount) for 
			obj, amount in self.countlets.iteritems()])

	@classmethod
	def from_array(cls, ar, objdir, constr):
		countlets = {}
		for line in ar:
			if len(line)==0:
				continue
			try:
				obj, amount = cls.countlet_from_line(line, 
						objdir, constr)
			except NoObjStrErr:
				continue
			## to get errors on all missing products
			#except ObjDirErr:
			#	continue
			if obj in countlets:
				raise MildErr("obj appears twice: '%s'"
						"(amount: %s)"
						% (obj, amount))
			countlets[obj] = amount
		return cls(countlets=countlets, constr=constr)
	
	@classmethod
	def countlet_from_line(cls, line, objdir, constr):
		if len(line)==0:
			raise ValueError("no object given")
		obj_str = line[0].strip()
		if(obj_str==""):
			raise NoObjStrErr()
		obj = objdir[obj_str]
		amount = None
		if len(line)==1:
			amount = 0
		else:
			amount_str = line[1].strip()
			try:
				amount = 0 if amount_str=="" \
						else constr(amount_str)
			except ValueError:
				raise MildErr("could not parse amount: '%s'" \
						% amount_str)
		return obj, amount

	def __add__(self, other):
		countlets = {}
		for a in (self, other):
			for obj in a.countlets.iterkeys():
				if obj not in countlets:
					countlets[obj] = self.constr(0)
				countlets[obj] += a[obj]
		return Count(countlets=countlets, constr=self.constr)
	
	def __neg__(self):
		countlets = {}
		for obj in self.countlets.iterkeys():
			countlets[obj] = -self.countlets[obj]
		return Count(countlets, self.constr)
	

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
			raise MildErr("Missing 'bar' title")
		if len(ar)==1 or len(ar[1])<6:
			raise MildErr("Incomplete/missing header")
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
		sell_count = Count.from_array(ar[2:], commodity_view, int)
		event = boozedir.eventdir[date]
		return cls(event=event, counter=counter, shift=shift,
				startbal=startbal, endbal=endbal,
				sell_count=sell_count, number=number,
				pricelist=pricelist)

	@property
	def date(self):
		return self.event.date

	# the amount of beer from the beertank counted
	@property
	def beertank(self):
		amount = 0
		for com in self.sell_count:
			pbt = com.product.beertank
			if pbt==0:
				continue
			amount += pbt * self.sell_count[com]
		return amount


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
				Count.zero(int))
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
				continue
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
		self.delivs = set()
		self.invcounts = set()
		self.bt_deliv = None
		self._beertank_event = None
		self._beertank_turfed = None
		self._beertank_used = None

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

	def register_deliv(self, deliv):
		self.delivs.add(deliv)
		if deliv.beertank!=0:
			if self.bt_deliv!=None:
				raise MildErr("double registration of "
						"beertank delivery")
			self.bt_deliv = deliv
	
	def register_invcount(self, ic):
		self.invcounts.add(ic)
	
	@property
	def shifts(self):
		return tuple(self.barforms.iterkeys())

	@property
	def beertank_turfed(self):
		if self._beertank_turfed==None:
			self._beertank_turfed = sum([bf.beertank 
				for bf in self.barforms.itervalues()])
		return self._beertank_turfed

	# returns the amount of bt-factors delivered to the beertank
	# during the event, or, if this is not available,
	# the amount read from the beertank display.
	@property
	def beertank_used(self):
		if self._beertank_used==None:
			self._beertank_used = self.bt_deliv.beertank \
				if self.bt_deliv!=None \
				else (self.btc if self.btc!=None else None)
		return self._beertank_used

	# returns whether this event used the beertank, 
	# like the monday socials.
	@property
	def beertank_activity(self):
		return self.beertank_used>0


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
		if len(ar)==0:
			raise MildErr("beertankcount.csv has no header")
		if len(ar[0])==0 or ar[0][0].lower()!="tap":
			raise MildErr("beertankcount.csv has faulty header: "
					"%s" % ar[0])
		count = Count.from_array(ar[1:], boozedir.eventdir,int)
		for event in count.countlets.iterkeys():
			event.register_btc(count[event])
		return count



class PriceList:
	def __init__(self, name, prices):
		self.prices = prices
		self.name = name

	def __repr__(self):
		return self.name

	@classmethod
	def from_path(cls, path, name, boozedir):
		ar = open_rikf_ar(path)
		return cls.from_array(ar, name, boozedir)

	@classmethod
	def from_array(cls, ar, name, boozedir):
		if len(ar)==0 or len(ar[0])==0 or \
				ar[0][0].lower()!="prijslijst":
			raise MildErr("Missing 'prijslijst' title")
		prices = Count.from_array(ar[1:], boozedir.productdir,Decimal)
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
		if name in self.pricelists:
			raise MildErr("pricelist with this"
					"name already exists.")
		return PriceList.from_path(path, name, self.boozedir)

	
	def __getitem__(self, name):
		if name not in self.pricelists:
			warn("Unknown pricelist: %s" % name)
			raise ObjDirErr()
		return self.pricelists[name]


class InvCount:
	def __init__(self, code, event, count):
		self.code = code
		self.event = event
		self.count = count
	
	@classmethod
	def from_path(cls, path, code, boozedir):
		return cls.from_array(open_rikf_ar(path), code, boozedir)


	@classmethod
	def from_array(cls, ar, code, boozedir):
		if len(ar)==0 or len(ar[0])==0:
			raise MildErr("no title")
		if ar[0][0].strip().lower()!="voorraadtelling":
			raise MildErr("title is not 'voorraadtelling'")
		if len(ar)==1 or len(ar[1])==0:
			raise MildErr("header is too small")
		header = ar[1]
		date = parse_date(header[0])
		event = boozedir.eventdir[date]
		count = Count.from_array(ar[2:], boozedir.productdir, int)
		return cls(code, event, count)


class InvCountDir:
	def __init__(self, path, boozedir):
		self.invcounts = {}
		self.boozedir = boozedir
		self.path = path
		self._load_invcounts()
	
	def _load_invcounts(self):
		for fn in listdir(self.path):
			comps, ignore = BoozeDir.processFn(fn)
			if ignore:
				continue
			try:
				ic = self._load_invcount(fn, comps)
				ic.event.register_invcount(ic)
			except MildErr as me:
				warn("failed to load inventory count '%s'"\
						% (fn,))
				continue
			self.invcounts[ic.code] = ic
	
	def _load_invcount(self, fn, comps):
		path = ospath.join(self.path, fn)
		code = ".".join(comps[0:-1])
		if code in self.invcounts:
			raise MildErr("inventory count with this "
					"name already exists.")
		return InvCount.from_path(path, code, self.boozedir)

	def __getitem__(self, code):
		if code not in self.invcounts:
			warn("Unknown inventory count: %s" % code)
			raise ObjDirErr()
		return self.invcounts[code]
	

class Deliv:
	def __init__(self, code, event, description, count):
		self.code = code
		self.event = event
		self.description = description
		self.count = count
		self._beertank = None

	@property
	def beertank(self):
		if self._beertank==None:
			amount = 0
			for com in self.count.countlets.keys():
				pbt = com.product.beertank
				if pbt==0:
					continue
				amount += self.count[com]*pbt
			self._beertank = amount
		return self._beertank
	

	@classmethod
	def from_path(cls, path, code, boozedir):
		return cls.from_array(open_rikf_ar(path), code, boozedir)


	@classmethod
	def from_array(cls, ar, code, boozedir):
		if len(ar)==0 or len(ar[0])==0:
			raise MildErr("no title")
		if ar[0][0].strip().lower()!="levering":
			raise MildErr("title is not 'levering'")
		if len(ar)==1 or len(ar[1])<=2:
			raise MildErr("header is too small")
		header = ar[1]
		try:
			pricelist = boozedir.pricelistdir[header[0].strip()]
		except ObjDirErr:
			raise MildErr("could not find pricelist")
		date = parse_date(header[1])
		event = boozedir.eventdir[date]
		description = header[2].strip().lower() if len(header)>=3 \
				else None
		view = boozedir.commoditydir.get_view(pricelist)
		count = Count.from_array(ar[2:], view, int)
		return cls(code, event, description, count)
		



class DelivDir:
	def __init__(self, path, boozedir):
		self.delivs = {}
		self.boozedir = boozedir
		self.path = path
		self._load_delivs()
	
	def _load_delivs(self):
		for fn in listdir(self.path):
			comps, ignore = BoozeDir.processFn(fn)
			if ignore:
				continue
			try:
				d = self._load_deliv(fn, comps)
				d.event.register_deliv(d)
			except MildErr as me:
				warn("failed to load delivery '%s': %s" \
						% (fn, me))
				continue
			self.delivs[d.code] = d
	
	def _load_deliv(self, fn, comps):
		path = ospath.join(self.path, fn)
		code = ".".join(comps[0:-1])
		if code in self.delivs:
			raise MildErr("delivery with this "
					"name already exists.")
		return Deliv.from_path(path, code, self.boozedir)

	def __getitem__(self, code):
		if code not in self.delivs:
			warn("Unknown delivery: %s" % code)
			raise ObjDirErr()
		return self.delivs[code]
	


class Commodity:
	def __init__(self, product, pricelist):
		self.product = product
		self.pricelist = pricelist
	
	def __hash__(self):
		return hash(self.product) ^ hash(self.pricelist)

	def __repr__(self):
		return "%s@%s" % (self.product, self.pricelist)


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
	# to compare to the beertankcounts
	btfactorhandle = "bav_tank"

	def __init__(self, path):
		self.eventdir = EventDir()
		self.beertankcount = \
				EventDir._load_btc_from_path(ospath.join(path,
			"beertankcount.csv"), self)
		self.factordir = FactorDir(ospath.join(path,
			"factor_catalog.csv"))
		self.productdir = ProductDir(ospath.join(path, 
			"product_catalog.csv"), self)
		self.invcountdir = InvCountDir(ospath.join(path,
			"inventory"), self)
		self.pricelistdir = PriceListDir(ospath.join(path,
			"pricelists"), self)
		self.commoditydir = CommodityDir(self)
		self.barformdir = BarFormDir(ospath.join(path,
			"barforms"), self)
		self.delivdir = DelivDir(ospath.join(path, 
			"deliverance"), self)


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

