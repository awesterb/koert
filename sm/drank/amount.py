# ad-hoc solution for parsing amounts in Counts
from common import MildErr

from decimal import Decimal

# parse the string representation  s  of an amount of the object  obj.
def parse_amount(s=None, obj=None):
	if s==None:
		return Decimal(0)
	term_strs = s.split("+")
	return sum(map(lambda ts: parse_amount_term(ts,obj), term_strs))

def parse_amount_term(t, obj):
	t = t.strip()
	if ":" not in t:
		return Decimal(t)
	command, args_str = t.split(":",2)
	res = getattr(obj, "parse_command", None)
	if res==None:
		raise MildErr("object '%r' does not support 'parse_command'"\
				% (obj,))
	return res(command, args_str)
