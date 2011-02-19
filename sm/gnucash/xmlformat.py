from core import Book, Account, Transaction, Split, TimeStamp, File, \
		Commodity
from koert.xml.sax.stacking import StackingHandler, CharactersSH, TimeSH, \
		IntSH, FractionSH
from koert.xml.sax.stacking.switch import SwitchSH
from koert.xml.sax.stacking.switch.cases import List as ListCase, \
		Dict as DictCase, Single as SingleCase, No as NoCase

class SaxHandler(StackingHandler):
	def __init__(self, scheme):
		self.scheme = scheme
		StackingHandler.__init__(self, PreGncSH())


class PreGncSH(SwitchSH):
	def __init__(self):
		SwitchSH.__init__(self, {"gnc-v2": SingleCase("gnc",GncSH)})

	def post_result(self, sh, result):
		SwitchSH.post_result(self, sh, result['gnc'])


class GncSH(SwitchSH):
	def __init__(self):
		SwitchSH.__init__(self, {
			"gnc:book": DictCase("books", BookSH, 
				lambda bk: bk.id),
			"gnc:count-data": NoCase})

	def post_result(self, sh, result):
		SwitchSH.post_result(self, sh, File(result))


class BookSH(SwitchSH):
	def __init__(self):
		SwitchSH.__init__(self, {
			"book:id": SingleCase("id", CharactersSH, True), 
			"gnc:account": DictCase("accounts",AccountSH,
				lambda ac: ac.id),
			"gnc:transaction": DictCase("transactions",
				TransactionSH, lambda tr: tr.id),
			"gnc:count-data": NoCase,
			"gnc:commodity": DictCase("commodities", CommoditySH, 
				lambda cm: cm.id),
			"gnc:budget": NoCase})
	
	def post_result(self, sh, result):
		SwitchSH.post_result(self, sh, Book(result, sh.scheme))


class CommoditySH(SwitchSH):
	def __init__(self):
		SwitchSH.__init__(self, {
			"cmdty:space": SingleCase("space", CharactersSH),
			"cmdty:id": SingleCase("id", CharactersSH, True),
			"cmdty:get_quotes": NoCase,
			"cmdty:quote_source": SingleCase("quote_source",
				CharactersSH),
			"cmdty:quote_tz": NoCase})
	
	def post_result(self, sh, result):
		SwitchSH.post_result(self, sh, Commodity(result))


class AccountSH(SwitchSH):
	def __init__(self):
		SwitchSH.__init__(self, {
			"act:name": SingleCase("name",CharactersSH, True),
			"act:id": SingleCase("id",CharactersSH, True),
			"act:type": SingleCase("type",CharactersSH, True),
			"act:parent": SingleCase("parent",CharactersSH),
			"act:description": SingleCase("description",
				CharactersSH),
			"act:code": SingleCase("code",CharactersSH),
			"act:commodity": SingleCase("commodity",
				CommoditySH),
			"act:commodity-scu": SingleCase("commodity-scu",
				IntSH),
			"act:slots": NoCase
			})

	def post_result(self, sh, result):
		SwitchSH.post_result(self, sh, Account(result))


class TransactionSH(SwitchSH):
	def __init__(self):
		SwitchSH.__init__(self, {
			"trn:id": SingleCase("id",CharactersSH, True),
			"trn:description": SingleCase("description",
				CharactersSH),
			"trn:num": SingleCase("num",CharactersSH),
			"trn:splits": SingleCase("splits",SplitsSH),
			"trn:currency": SingleCase("currency", 
				CommoditySH, True),
			"trn:slots": NoCase,
			"trn:date-posted": SingleCase(
				"date-posted",TimeStampSH),
			"trn:date-entered": SingleCase(
				"date-entered",TimeStampSH)})

	def post_result(self, sh, result):
		SwitchSH.post_result(self, sh, Transaction(result))


class SplitsSH(SwitchSH):
	def __init__(self):
		SwitchSH.__init__(self, {
			"trn:split": DictCase("splits",SplitSH,lambda s: s.id)})
	
	def post_result(self, sh, result):
		SwitchSH.post_result(self, sh, result['splits'])


class SplitSH(SwitchSH):
	def __init__(self):
		SwitchSH.__init__(self, {
			"split:id":  SingleCase("id",CharactersSH,True),
			"split:value": SingleCase("value",FractionSH, True),
			"split:quantity": SingleCase("quantity",
				FractionSH,True),
			"split:account": SingleCase("account", 
				CharactersSH, True),
			"split:memo": SingleCase("memo",CharactersSH),
			"split:reconciled-state": SingleCase(
				"reconciled-state",CharactersSH)
			})

	def post_result(self, sh, result):
		SwitchSH.post_result(self, sh, Split(result))


class TimeStampSH(SwitchSH):
	def __init__(self):
		SwitchSH.__init__(self, {
			"ts:date": SingleCase("date",TimeSH,True),
			"ts:ns": SingleCase("ns",IntSH)
			})
	
	def post_result(self, sh, result):
		SwitchSH.post_result(self, sh, TimeStamp(result))
