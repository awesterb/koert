from common import MildErr, LoadErr, ObjDirErr,\
		parse_int, parse_date, parse_decimal, processFn
from count import Count
from rikf import open_rikf_ar
from amount import parse_amount

import datetime
from os import listdir
from os import path as ospath
from warnings import warn
from decimal import Decimal

class Shift:
	def __init__(self, number=None, label=None):
		self.number = number
		self.label = label
	
	def __repr__(self):
		return "Shift(%s,%s)" % (self.number, self.label)

	def __str__(self):
		res = str(self.number) if self.number else "?"
		if self.label:
			res += " (%s)" % (self.label,)
		return res

	@classmethod
	def from_str(cls, s):
		# The grammar:  <number>[/<label>]
		s = s.strip()
		if not s:
			return cls()
		parts = s.split("/",1)
		number = parse_int(parts[0])
		if len(parts)==1:
			return cls(number)
		label = parts[1]
		return cls(number,label)


class Event:
	def __init__(self, date):
		self.date = date
		self.barforms = {}
		self.btc = None
		self.delivs = set()
		self.invcount = None
		self.bt_deliv = None
		self._beertank_event = None
		self._beertank_turfed = None
		self._beertank_used = None

	def __str__(self):
		return "@"+("unspecified-time"
				if self.date==None else str(self.date))

	@property
	def all_barforms(self):
		for l in self.barforms:
			for i in self.barforms[l]:
				yield self.barforms[l][i]
	
	def register_barform(self, barform):
		shift = barform.shift
		l = shift.label
		if l not in self.barforms:
			self.barforms[l] = dict()
		n = shift.number
		if shift.number in self.barforms[l]:
			raise MildErr("shift already taken: %s at %s by %s" 
					% (shift, self.date, 
						self.barforms[l][n]))
		self.barforms[l][n] = barform

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
		if self.invcount:
			raise MildErr("double registration of invcount: "\
					"%s and %s" % (self.invcount, ic))
		self.invcount = ic
	
	@property
	def shifts(self):
		return tuple(self.barforms.iterkeys())

	@property
	def beertank_turfed(self):
		if self._beertank_turfed==None:
			self._beertank_turfed = sum([bf.beertank 
				for bf in self.all_barforms])
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
		self.periods = []
	
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
		count = Count.from_array(ar[1:], boozedir.eventdir,
				parse_amount)
		for event in count.countlets.iterkeys():
			event.register_btc(count[event])
		return count

	def get_in_interval(self, start, end):
		for ev in self.events.itervalues():
			if start <= ev.date <= end:
				yield ev
	
	def create_periods(self):
		dates =  self.events.keys()
		dates.sort()
		# indices of dates with an inventory count
		idcs = [i for i in range(len(dates)) 
				if self.events[dates[i]].invcount]
		N = len(idcs)-1  # number of periods
		if N == -1:
			self.periods = []
			return
		periods = [None] * N
		for n in xrange(N):
			start_idx = idcs[n]
			end_idx = idcs[n+1]
			start_ic = self.events[dates[start_idx]].invcount
			end_ic = self.events[dates[end_idx]].invcount
			p_idcs = range(start_idx, end_idx+1)
			p_events = map(lambda idx: self.events[dates[idx]],
					p_idcs)
			periods[n] = Period(n, start_ic, end_ic, p_events)
		self.periods = periods


# A period between two inventory counts,
# which is like an accounting period;
# the start and ending inventory counts act as starting and closing balance.
class Period:
	def __init__(self, number, start_ic, end_ic, events):
		self.start_ic = start_ic
		self.end_ic = end_ic
		self.number = number
		self.events = dict()
		for event in events:
			self.events[event.date] = event
		self._ftallied = None
		self._fdelivered = None
	
	@property
	def start_date(self):
		return self.start_ic.event.date

	@property
	def end_date(self):
		return self.end_ic.event.date

	def __str__(self):
		return "Period #%s %s -- %s" % (self.number,
				self.start_date, self.end_date)

	@property
	def barforms(self):
		for event in self.events.itervalues():
			for bf in event.all_barforms:
				yield bf
	
	@property
	def delivs(self):
		for event in self.events.itervalues():
			for dl in event.delivs:
				yield dl

	@property
	def ftallied(self):
		return sum(map(lambda bf: bf.total_factors, self.barforms),
				Count.zero(parse_amount))
	
	@property
	def fdelivered(self):
		return sum(map(lambda dl: dl.total_factors, self.delivs),
				Count.zero(parse_amount))


class BarForm:
	def __init__(self, event, counter, shift, sell_count, 
			startbal, endbal, number, pricelist, mutation):
		self.event = event
		self.counter = counter
		self.shift = shift
		self.startbal = int(startbal*100)
		self.endbal = int(endbal*100)
		self.sell_count = sell_count
		self.number = number
		self.pricelist = pricelist
		self.mutation = mutation
	
	def __str__(self):
		return "bf%s" % (self.number,)

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
		#   pricelist; date ; counter ; shift# ; 
		#        startbal ; endbal [; mutation ]
		#
		# Here: mutation the amount transferred to the
		# cash register during the shift.  For istance,
		# an "afroming" during a shift would lower this number.
		header = ar[1]
		pricelist_str = header[0]
		pricelist = boozedir.pricelistdir[pricelist_str]
		date = parse_date(header[1])
		counter = header[2]
		shift = Shift.from_str(header[3])
		startbal = parse_decimal(header[4])
		endbal = parse_decimal(header[5])
		mutation = parse_decimal(header[6]) if len(header)>6 \
				else Decimal(0)
		# below, to translate "product@pricelist" to a commodity
		commodity_view = boozedir.commoditydir.get_view(pricelist)
		sell_count = Count.from_array(ar[2:], commodity_view, 
				parse_amount)
		event = boozedir.eventdir[date]
		return cls(event=event, counter=counter, shift=shift,
				startbal=startbal, endbal=endbal,
				sell_count=sell_count, number=number,
				pricelist=pricelist,
				mutation=mutation)

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

	@property
	def total_factors(self):
		return self.sell_count.map(
				lambda c,n: c.product.factors.scale(n).items)

	@property
	def amount_turfed(self):
		return self.sell_count.total(lambda c: c.price)

	@property
	def amount_cashed(self):
		return self.endbal - self.startbal - self.mutation


class BarFormDir:
	def __init__(self, path, boozedir):
		self.barforms = {}
		self.boozedir = boozedir
		self.path = path
		self._total_sold = None
		self._total_factors = None
		self._load_barforms()
	
	@property
	def total_sold(self):
		if self._total_sold==None:
			self._total_sold = sum([bf.sell_count 
				for bf in self.all_barforms],
				Count.zero(parse_amount))
		return self._total_sold

	@property
	def total_factors(self):
		if self._total_factors==None:
			self._total_factors = sum([bf.total_factors
				for bf in self.barforms.values()],
				Count.zero(int))
		return self._total_factors
	
	def _load_barforms(self):
		self.barforms = {}
		errors = []
		for fn in listdir(self.path):
			if not ospath.isfile(ospath.join(self.path, fn)):
				continue
			comps, ignore = processFn(fn)
			if ignore:
				continue
			try:
				bf = self._load_barform(fn, comps)
				bf.event.register_barform(bf)
			except MildErr as me:
				errors.append(LoadErr("barform", fn, me))
				continue
			self.barforms[bf.number] = bf
		if len(errors)>0:
			warn("Failed to load some barforms: \n\t%s" 
					% '\n\t'.join(map(repr,errors)))

	def _load_barform(self, fn, comps):
		number = comps[0]
		path = ospath.join(self.path, fn)
		if number in self.barforms:
			raise ValueError("double number")
		return BarForm.from_path(path, number, self.boozedir)


class InvCount:
	def __init__(self, code, event, count):
		self.code = code
		self.event = event
		self.count = count
	
	def __str__(self):
		return self.code
	
	@classmethod
	def from_path(cls, path, code, boozedir):
		return cls.from_array(open_rikf_ar(path), code, boozedir)


	@classmethod
	def from_array(cls, ar, code, boozedir):
		if len(ar)==0 or len(ar[0])==0:
			raise MildErr("no title")
		if ar[0][0].lower()!="voorraadtelling":
			raise MildErr("title is not 'voorraadtelling'")
		if len(ar)==1 or len(ar[1])==0:
			raise MildErr("header is too small")
		header = ar[1]
		date = parse_date(header[0])
		event = boozedir.eventdir[date]
		count = Count.from_array(ar[2:], boozedir.productdir, 
				parse_amount)
		return cls(code, event, count)


class InvCountDir:
	def __init__(self, path, boozedir):
		self.invcounts = {}
		self.boozedir = boozedir
		self.path = path
		self._load_invcounts()
	
	def _load_invcounts(self):
		errors = []
		for fn in listdir(self.path):
			comps, ignore = processFn(fn)
			if ignore:
				continue
			try:
				ic = self._load_invcount(fn, comps)
				ic.event.register_invcount(ic)
			except MildErr as me:
				errors.append(LoadErr('inventory-count',
					fn, me))
				continue
			self.invcounts[ic.code] = ic
		if len(errors)>0:
			warn("Failed to load some inventory counts: \n\t%s"
					% "\n\t".join(map(repr,errors)))
	
	def _load_invcount(self, fn, comps):
		path = ospath.join(self.path, fn)
		code = ".".join(comps[0:-1])
		if code in self.invcounts:
			raise MildErr("inventory count with this "
					"name already exists.")
		return InvCount.from_path(path, code, self.boozedir)

	def __getitem__(self, code):
		if code not in self.invcounts:
			raise ObjDirErr("inventory-count", code)
		return self.invcounts[code]
	

class DelivErr(MildErr):
	def __str__(self):
		return "error concerning delivery %s:\n  %s" % self.args

class Deliv:
	def __init__(self, code, event, description, count, board=False):
		self.code = code
		self.event = event
		self.description = description
		self.count = count
		self.board = board
		self._beertank = None

	def __repr__(self):
		return self.code

	@property
	def price(self):
		try:
			return self.count.total(lambda x: x.price)
		except MildErr as e:
			raise DelivErr(self, e)

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
	def from_path(cls, path, code, boozedir, board):
		return cls.from_array(open_rikf_ar(path), code, boozedir, board)


	@classmethod
	def from_array(cls, ar, code, boozedir, board):
		if len(ar)==0 or len(ar[0])==0:
			raise MildErr("no title")
		if ar[0][0].lower()!="levering":
			raise MildErr("title is not 'levering'")
		if len(ar)==1 or len(ar[1])<2:
			raise MildErr("header is too small")
		header = ar[1]
		try:
			pricelist = boozedir.pricelistdir[header[0]]
		except ObjDirErr:
			raise MildErr("could not find pricelist")
		date = parse_date(header[1])
		event = boozedir.eventdir[date]
		description = header[2].lower() if len(header)>=3 \
				else None
		view = boozedir.commoditydir.get_view(pricelist)
		count = Count.from_array(ar[2:], view, parse_amount)
		return cls(code, event, description, count, board)
		
	@property
	def total_factors(self):
		return self.count.map(
				lambda c,n: c.product.factors.scale(n).items)



class DelivDir:
	def __init__(self, deliv_path, board_path, boozedir):
		self.delivs = {}
		self.boozedir = boozedir
		self.deliv_path = deliv_path
		self.board_path = board_path
		self._load_delivs(deliv_path, False)
		self._load_delivs(board_path, True)
		self._total_factors = None

	
	def _load_delivs(self, path, board):
		errors = []
		for fn in listdir(path):
			comps, ignore = processFn(fn)
			if ignore:
				continue
			try:
				d = self._load_deliv(path, fn, comps, board)
				d.event.register_deliv(d)
			except MildErr as me:
				errors.append(LoadErr("delivery", fn, me))
				continue
			self.delivs[d.code] = d
		if len(errors)>0:
			warn("Failed to load some deliveries: \n\t%s"
					% '\n\t'.join(map(repr, errors)))
	
	def _load_deliv(self, dpath, fn, comps, board):
		path = ospath.join(dpath, fn)
		code = ".".join(comps[0:-1])
		if code in self.delivs:
			raise MildErr("delivery with this "
					"name already exists.")
		return Deliv.from_path(path, code, self.boozedir, board)

	def __getitem__(self, code):
		if code not in self.delivs:
			raise ObjDirErr("delivery",code)
		return self.delivs[code]

	def __iter__(self):
		return iter(self.delivs.itervalues())
	
	@property
	def total_factors(self):
		if self._total_factors==None:
			self._total_factors = sum([bf.total_factors
				for bf in self.delivs.itervalues()],
				Count.zero(parse_amount))
		return self._total_factors
