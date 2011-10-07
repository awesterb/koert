from xml.sax.handler import ContentHandler as SaxHandler
from decimal import Decimal
import time


class StackingHandler(SaxHandler):
	def __init__(self, init_handler_type):
		self.current_depth = 0
		self.stack = []
		self.result = None
		self.handler_lut = dict()
		self.current_handler \
				= self.get_handler_instance(init_handler_type)

	def startElement(self, name, attrs):
		new_handler_type = self.current_handler.startElement(self, 
				name, attrs)
		if new_handler_type==None:
			self.current_depth += 1
			return
		self.stack.append((self.current_handler, self.current_depth))
		self.current_handler \
				= self.get_handler_instance(new_handler_type)
		self.current_depth = 0

	def endElement(self, name):
		if self.current_depth:
			self.current_depth -= 1
			self.current_handler.endElement(self, name, None)
			return
		spawned_handler = self.current_handler
		spawned_handler.goodbye(self)
		self.current_handler, self.current_depth = self.stack.pop()
		self.current_handler.endElement(self, name, spawned_handler)
		self.try_to_reclaim(spawned_handler)
	
	def characters(self, content):
		self.current_handler.characters(self, content)

	def endDocument(self):
		assert(not self.current_depth)
		assert(not len(self.stack))
		self.current_handler.goodbye(self)
		self.result = self.current_handler.result

	def get_handler_instance(self, handler_type):
		handler = self.lookup_handler_instance(handler_type)
		if handler==None:
			return handler_type(handler_type)
		return handler
	
	def lookup_handler_instance(self, handler_type):
		if handler_type not in self.handler_lut:
			return None
		list_of_instances = self.handler_lut[handler_type]
		if len(list_of_instances)==0:
			return None
		handler = list_of_instances.pop()
		return handler

	def try_to_reclaim(self, handler):
		if not handler.reclaim():
			return
		ht = handler.orig_type
		if not ht in self.handler_lut:
			self.handler_lut[ht]=list()
		self.handler_lut[ht].append(handler)

class SH(object):
	def __init__(self, orig_type):
		self.result = None
		self.orig_type = orig_type
	def startElement(self, sh, name, attrs):
		return None
	def endElement(self, sh, name, spawned_handler):
		pass
	def characters(self, sh, content):
		pass
	def goodbye(self, sh):
		pass
	def reclaim(self):
		return False
	def post_result(self, sh, result):
		self.result = result


class CharactersSH(SH):
	def __init__(self, ot):
		SH.__init__(self, ot)
		self.pieces = []
	def characters(self, sh, content):
		self.pieces.append(content)
	def goodbye(self, sh):
		self.post_result(sh, self._tweak_result(''.join(self.pieces)))
	def _tweak_result(self, result):
		return result
	def reclaim(self):
		del self.pieces[:]
		self.result=None
		return True

# todo: parse offset; unfortunately, time.strptime does not support 
#       the %z directive
time_format = "%Y-%m-%d %H:%M:%S"
class TimeSH(CharactersSH):
	def __init__(self, ot):
		CharactersSH.__init__(self, ot)
	def _tweak_result(self, result):
		if "+" in result:
			result,offset = result.split("+")
		return time.mktime(time.strptime(result.strip(), time_format))

class IntSH(CharactersSH):
	def __init__(self, ot):
		CharactersSH.__init__(self, ot)
	def _tweak_result(self, result):
		return int(result)

class FractionSH(CharactersSH):
	def __init__(self, ot):
		CharactersSH.__init__(self, ot)
	def _tweak_result(self, result):
		d, n = map(int,result.split("/"))
		return Decimal(d)/Decimal(n)

class PrintSH(SH):
	def __init__(self, ot):
		SH.__init__(self, ot)

	def startElement(self, sh, name, attrs):
		print " "*sh.current_depth + name
		return None
	
	def endElement(self, sh, name, spawned_handler):
		print " "*sh.current_depth + name



