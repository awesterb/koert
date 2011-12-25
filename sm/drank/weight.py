from common import parse_int
from rikf import open_rikf_ar

from decimal import Decimal

class WeightDir:
	def __init__(self, path, boozedir):
		weights = {}
		self.boozedir = boozedir
		self.path = path
		ar = open_rikf_ar(path)
		for line in ar:
			weight = Weight.from_line(line, boozedir.productdir)
			product = weight.product
			if product in weights:
				raise ValueError("weight of product appears "
					"twice: %s" % (product,))
			weights[product] = weight
			product.weight = weight
		self.weights = weights

	def __repr__(self):
		return "Weight Directory"


class Weight:
	def __init__(self, product, full, empty):
		self.product = product
		self.full = full
		self.empty = empty

	@classmethod
	def from_line(cls, line, productdir):
		if len(line)<3:
			raise ValueError("weight line is too small")
		product_str, empty_str, full_str = line[0:3]
		product = productdir[product_str]
		full = parse_int(full_str)
		empty = parse_int(empty_str)
		return cls(product, full, empty)

	@property
	def content(self):
		return self.full - self.empty

	def weighed_to_fraction(self, weighed):
		return Decimal(weighed - self.empty) \
				/ Decimal(self.content)

	def __repr__(self):
		return "Weight(%r,%r,%r)" % (self.product,
				self.empty, self.full)

	def __hash__(self):
		return hash((self.product, self.empty, self.full))

