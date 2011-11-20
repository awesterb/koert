from rikf import open_rikf_ar
from count import Count
from common import MildErr, ManyMildErrs, ObjDirErr, LoadErr, DoubleErr,\
		parse_int, load_kwargs
from event import EventDir

import datetime
from os import listdir, path as ospath
import decimal
from warnings import warn

class Factor:
	def __init__(self, handle, name, beertank=False):
		self.handle = handle
		self.name = name
		self.beertank = beertank
	
	@classmethod
	def from_line(cls, line):
		if len(line)<1:
			raise ValueError("factor line is too small")
		handle, name = line[0:2]
		kwargs = load_kwargs(line[2:], beertank=bool)
		return cls(handle=handle, name=name, **kwargs)

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
			field = line[i]
			if field=="":
				break
			comps = field.split(":")
			if(len(comps)!=2):
				raise ValueError("error in factor multiple's"
						" formatting; components: "
						" %s " % (comps,) + "; "
						"did you forget a colon?")
			amount_str, factor_name = comps
			amount = parse_int(amount_str)
			factor = boozedir.factordir[factor_name]
			if factor in factors:
				raise ValueError("factor occurs twice")
			factors[factor] = amount
		if len(factors)==0:
			raise MildErr("product %s (%s) has no factors" 
					% (handle, name))
		return cls(handle=handle, name=name, 
				factors=Count(factors, parse_int))

	def __repr__(self):
		return self.handle

	def __hash__(self):
		return hash(self.handle)^hash(self.name)

	def factors_scaled(self, sc):
		return self.factors.map(lambda k,v: ((k,v*sc),))

	@property
	def beertank(self):
		for f in self.factors:
			if not f.beertank:
				continue
			return self.factors[f]
		return self.factors.constr(0)


class ProductDir:
	def __init__(self, path, boozedir):
		errors = []
		products = {}
		self.boozedir = boozedir
		self.path = path
		ar = open_rikf_ar(path)
		for line in ar:
			try:
				product = Product.from_line(line, self.boozedir)
			except MildErr as e:
				errors.append(LoadErr("product", 
					line, e))
				continue
			handle = product.handle
			if handle in products:
				errors.append(DoubleErr("product handle",
					handle))
				continue
			products[handle]=product
		self.products = products
		if len(errors)>0:
			warn("Errors when loading the product directory: %s" 
					% ManyMildErrs(errors))

	def __repr__(self):
		return "Product Directory"

	def __getitem__(self, name):
		if name not in self.products:
			raise ObjDirErr("product", name)
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
			raise ObjDirErr("factor",name)
		return self.factors[name]
	
	def __contains__(self, name):
		return name in self.factors


