from __future__ import absolute_import
from .core import Book, Account, Transaction, Split, TimeStamp, File, \
    Commodity
from koert.sax.core import StackingHandler, CharactersSH, TimeSH, \
    IntSH, FractionSH
from koert.sax.switch import SwitchSH, DictCase, SingleCase, NoCase


class SaxHandler(StackingHandler):

    def __init__(self):
        StackingHandler.__init__(self, PreGncSH)


class PreGncSH(SwitchSH):

    def __init__(self, ot):
        SwitchSH.__init__(self, ot, {"gnc-v2": SingleCase("gnc", GncSH)})

    def post_result(self, sh, result):
        SwitchSH.post_result(self, sh, result['gnc'])


class GncSH(SwitchSH):

    def __init__(self, ot):
        SwitchSH.__init__(self, ot, {
            "book": DictCase("books", BookSH,
                             lambda bk: bk.id),
            "count-data": NoCase})

    def post_result(self, sh, result):
        SwitchSH.post_result(self, sh, File(result))


class BookSH(SwitchSH):

    def __init__(self, ot):
        SwitchSH.__init__(self, ot, {
            "id": SingleCase("id", CharactersSH, True),
            "account": DictCase("accounts", AccountSH,
                                lambda ac: ac.id),
            "transaction": DictCase("transactions",
                                    TransactionSH, lambda tr: tr.id),
            "count-data": NoCase,
            "commodity": DictCase("commodities", CommoditySH,
                                  lambda cm: cm.id),
            "budget": NoCase})

    def post_result(self, sh, result):
        SwitchSH.post_result(self, sh, Book(result))


class CommoditySH(SwitchSH):

    def __init__(self, ot):
        SwitchSH.__init__(self, ot, {
            "space": SingleCase("space", CharactersSH),
            "id": SingleCase("id", CharactersSH, True),
            "get_quotes": NoCase,
            "quote_source": SingleCase("quote_source",
                                       CharactersSH),
            "quote_tz": NoCase})

    def post_result(self, sh, result):
        SwitchSH.post_result(self, sh, Commodity(result))


class AccountSH(SwitchSH):

    def __init__(self, ot):
        SwitchSH.__init__(self, ot, {
            "name": SingleCase("name", CharactersSH, True),
            "id": SingleCase("id", CharactersSH, True),
            "type": SingleCase("type", CharactersSH, True),
            "parent": SingleCase("parent", CharactersSH),
            "description": SingleCase("description",
                                      CharactersSH),
            "code": SingleCase("code", CharactersSH),
            "commodity": SingleCase("commodity",
                                    CommoditySH),
            "commodity-scu": SingleCase("commodity-scu",
                                        IntSH),
            "slots": NoCase
        })

    def post_result(self, sh, result):
        SwitchSH.post_result(self, sh, Account(result))


class TransactionSH(SwitchSH):

    def __init__(self, ot):
        SwitchSH.__init__(self, ot, {
            "id": SingleCase("id", CharactersSH, True),
            "description": SingleCase("description",
                                      CharactersSH),
            "num": SingleCase("num", CharactersSH),
            "splits": SingleCase("splits", SplitsSH),
            "currency": SingleCase("currency",
                                   CommoditySH, True),
            "slots": NoCase,
            "date-posted": SingleCase(
                "date-posted", TimeStampSH),
            "date-entered": SingleCase(
                "date-entered", TimeStampSH)})

    def post_result(self, sh, result):
        SwitchSH.post_result(self, sh, Transaction(result))


class SplitsSH(SwitchSH):

    def __init__(self, ot):
        SwitchSH.__init__(self, ot, {
            "split": DictCase("splits", SplitSH, lambda s: s.id)})

    def post_result(self, sh, result):
        SwitchSH.post_result(self, sh, result['splits'])


class SplitSH(SwitchSH):

    def __init__(self, ot):
        SwitchSH.__init__(self, ot, {
            "id": SingleCase("id", CharactersSH, True),
            "value": SingleCase("value", FractionSH, True),
            "quantity": SingleCase("quantity",
                                   FractionSH, True),
            "account": SingleCase("account",
                                  CharactersSH, True),
            "memo": SingleCase("memo", CharactersSH),
            "reconciled-state": SingleCase(
                "reconciled-state", CharactersSH)
        })

    def post_result(self, sh, result):
        SwitchSH.post_result(self, sh, Split(result))


class TimeStampSH(SwitchSH):

    def __init__(self, ot):
        SwitchSH.__init__(self, ot, {
            "date": SingleCase("date", TimeSH, True),
            "ns": SingleCase("ns", IntSH)
        })

    def post_result(self, sh, result):
        SwitchSH.post_result(self, sh, TimeStamp(result))
