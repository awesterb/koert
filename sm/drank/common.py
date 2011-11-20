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

# process file name: 
#   split it into "."-seperated components,
#   returns these and whether to ignore the file.
def processFn(fn):
	comps = fn.split(".")
	if len(fn)==0:
		return comps, True
	if fn[0]==".":
		return comps, True
	if len(comps)>1:
		if comps[-1][-1]=="~" or comps[-1][-1]=="swp":
			return comps, True
		if comps[0] in ('template','example'):
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
	
