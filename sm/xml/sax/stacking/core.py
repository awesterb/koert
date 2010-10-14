from xml.sax.handler import ContentHandler as SaxHandler
from decimal import Decimal
import time


class StackingHandler(SaxHandler):
	def __init__(self, init_handler):
		self.current_handler = init_handler
		self.current_depth = 0
		self.stack = []
		self.result = None

	def startElement(self, name, attrs):
		new_handler = self.current_handler.startElement(self, 
				name, attrs)
		if not new_handler:
			self.current_depth += 1
			return
		self.stack.append((self.current_handler, self.current_depth))
		self.current_handler = new_handler
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
	
	def characters(self, content):
		self.current_handler.characters(self, content)

	def endDocument(self):
		assert(not self.current_depth)
		assert(not len(self.stack))
		self.current_handler.goodbye(self)
		self.result = self.current_handler.result


class SH(object):
	def __init__(self):
		self.result = None
	def startElement(self, sh, name, attrs):
		return None
	def endElement(self, sh, name, spawned_handler):
		pass
	def characters(self, sh, content):
		pass
	def goodbye(self, sh):
		pass
	def post_result(self, sh, result):
		self.result = result


class CharactersSH(SH):
	def __init__(self):
		SH.__init__(self)
		self.pieces = []
	def characters(self, sh, content):
		self.pieces.append(content)
	def goodbye(self, sh):
		self.post_result(sh, self._tweak_result(''.join(self.pieces)))
	def _tweak_result(self, result):
		return result

# todo: parse offset; unfortunately, time.strptime does not support 
#       the %z directive
time_format = "%Y-%m-%d %H:%M:%S +0200"
class TimeSH(CharactersSH):
	def __init__(self):
		CharactersSH.__init__(self)
	def _tweak_result(self, result):
		return time.mktime(time.strptime(result.strip(), time_format))

class IntSH(CharactersSH):
	def __init__(self):
		CharactersSH.__init__(self)
	def _tweak_result(self, result):
		return int(result)

class FractionSH(CharactersSH):
	def __init__(self):
		CharactersSH.__init__(self)
	def _tweak_result(self, result):
		d, n = map(int,result.split("/"))
		return Decimal(d)/Decimal(n)

class PrintSH(SH):
	def __init__(self):
		SH.__init__(self)

	def startElement(self, sh, name, attrs):
		print " "*sh.current_depth + name
		return None
	
	def endElement(self, sh, name, spawned_handler):
		print " "*sh.current_depth + name



