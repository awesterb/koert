from common import MildErr, processFn, parse_decimal
from count import Count
from rikf import open_rikf_ar

from os import listdir
from os import path as ospath

class PriceListErr(MildErr):
	def __str__(self):
		return "'%s' has no price in %s." % self.args


class PriceList:
	def __init__(self, name, prices):
		self.prices = prices
		self.name = name

	def __repr__(self):
		return self.name

	def __getitem__(self, obj):
		try:
			return self.prices[obj]
		except KeyError:
			raise PriceListErr(self, obj)

	@classmethod
	def from_path(cls, path, name, boozedir):
		ar = open_rikf_ar(path)
		return cls.from_array(ar, name, boozedir)

	@classmethod
	def from_array(cls, ar, name, boozedir):
		if len(ar)==0 or len(ar[0])==0 or \
				ar[0][0].lower()!="prijslijst":
			raise MildErr("Missing 'prijslijst' title")
		prices = Count.from_array(ar[1:], boozedir.productdir,
				parse_decimal)
		return cls(name=name,prices=prices)


class PriceListDir:
	def __init__(self, path, boozedir):
		self.pricelists = {}
		self.boozedir = boozedir
		self.path = path
		self._load_pricelists()
	
	def _load_pricelists(self):
		errors = []
		for fn in listdir(self.path):
			comps, ignore = processFn(fn)
			if ignore:
				continue
			try:
				bf = self._load_pricelist(fn, comps)
			except MildErr as me:
				errors.append(LoadErr("pricelist", fn, me))
				continue
			self.pricelists[bf.name] = bf
		if len(errors)>0:
			warn("Failed to load some pricelists: \n\t%s" 
				% "\n\t".join(map(repr,errors)))
	
	def _load_pricelist(self, fn, comps):
		path = ospath.join(self.path, fn)
		name = '.'.join(comps[0:-1])
		if name in self.pricelists:
			raise MildErr("pricelist with this"
					"name already exists.")
		return PriceList.from_path(path, name, self.boozedir)

	
	def __getitem__(self, name):
		if name not in self.pricelists:
			raise ObjDirErr("pricelist", name)
		return self.pricelists[name]	


class Commodity:
	def __init__(self, product, pricelist):
		self.product = product
		self.pricelist = pricelist
	
	@property
	def price(self):
		return self.pricelist[self.product]
	
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


