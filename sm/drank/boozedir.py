from core import FactorDir, ProductDir
from event import EventDir, InvCountDir, BarFormDir, DelivDir
from pricelist import PriceListDir, CommodityDir
from weight import WeightDir

from os import path as ospath


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
		self.weightdir = WeightDir(ospath.join(path,
			"weights.csv"), self)
		self.invcountdir = InvCountDir(ospath.join(path,
			"inventory"), self)
		self.eventdir.create_periods()
		self.pricelistdir = PriceListDir(ospath.join(path,
			"pricelists"), self)
		self.commoditydir = CommodityDir(self)
		self.barformdir = BarFormDir(ospath.join(path,
			"barforms"), self)
		self.delivdir = DelivDir(
				ospath.join(path, "deliverance"), 
				ospath.join(path, "board"), self)

