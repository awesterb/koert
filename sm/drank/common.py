import datetime
import decimal

# We often ignore the following errors
class MildErr(Exception):
	pass

class ManyMildErrs(MildErr):
	pass

class LoadErr(MildErr):
	def __repr__(self):
		return "Failed to load %s '%s': %s" % self.args

class DoubleErr(MildErr):
	def __repr__(self):
		return "This %s appears twice: %s" % self.args


# raised when, e.g., product does not appear in productdir.
class ObjDirErr(MildErr):
	def __str__(self):
		return "Unknown %s: %s" % self.args

def parse_int(s):
	try:
		return int(s)
	except ValueError as v:
		raise MildErr("failed to parse int: %s" % (v,))

def parse_decimal(s):
	s = s.strip()
	if s=='onbekend':
		return None
	try:
		return decimal.Decimal(s)
	except decimal.InvalidOperation as e:
		raise MildErr("failed to parse decimal: %s" % (e,))

def parse_date(date_str):
	if date_str=="":
		date = None
	else:
		a,b,c = map(parse_int, date_str.split("-"))
		year, month, day = (a,b,c) if a>100 else (c,b,a)
		date = datetime.date(year, month, day)
	return date

# A moment has the following grammar:  <date>[/<number:int>]
def parse_moment(moment_str):
	parts = moment_str.split("/")
	date = parse_date(parts[0])
	if len(parts) not in (1,2):
		raise ValueError("Invalid moment: %s" % (moment_str,))
	number = parse_int(parts[1]) if len(parts)==2 else None
	return Moment(date, number)

class Moment:
	def __init__(self, date, number=None):
		self.date = date
		self.number = number
	
	def __str__(self):
		first = self.date.strftime("%Y-%m-%d") if self.date else "?"
		if self.number:
			return "%s/%s" % (first, self.number)
		return first

	# Moments are ordered lexicographicallish with the important
	# exception that e.g.
	# 	2011-10-12/3 <= 2011-10-12
	def __cmp__(self, other):
		dd = cmp(self.date, other.date)
		if dd != 0:
			return dd
		# self and other occur on the same date
		if not other.number:
			if not self.number:
				return 0
			# self has a number, but other does not, 
			#   so self is smaller than other
			return -1
		if not self.number:
			# self has no number, but other does,
			#   so self is larger than other
			return 1
		return cmp(self.number, other.number)

	def __eq__(self, other):
		if not isinstance(self, Moment):
			return NotImplemented
		if not isinstance(other, Moment):
			return False
		return (self.date, self.number) == (other.date, other.number)

	def __hash__(self):
		return hash((self.date, self.number))


# process file name: 
#   split it into "."-seperated components,
#   returns these and whether to ignore the file.
def processFn(fn):
	comps = fn.split(".")
	# ignore ".hidden" files
	if len(comps)==0 or comps[0]=="": 
		return comps, True
	if comps[0] in ('template','example'):
		return comps, True
	if comps[-1] not in ("csv",):
		return comps, True
	return comps, False

# ["a=b",...], a=A, ...  -> {"a":A(b), ...}
def load_kwargs(l, **handlers):
	ret = dict()
	for p in l:
		k,v = load_kwarg(p, **handlers)
		ret[k]=v
	return ret

def load_kwarg(p, **handlers):
	k,raw_v = p.split("=")
	if k not in handlers:
		raise ValueError("Expected one of %s, but got %s"
				% (handlers.keys(),k))
	return k,handlers[k](raw_v)
	
