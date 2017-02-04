import six
from datetime import datetime
import re


class GcStruct(object):

    def __init__(self, fields):
        self.fields = fields


class GcObj(GcStruct):

    def __init__(self, fields):
        GcStruct.__init__(self, fields)

    @property
    def id(self):
        return self.fields['id']


class File(GcStruct):

    def __init__(self, fields):
        GcStruct.__init__(self, fields)

    @property
    def books(self):
        return self.fields['books']

    @property
    def book(self):
        return list(self.books.values())[0]


class Book(GcObj):

    def __init__(self, fields):
        GcObj.__init__(self, fields)
        self._root = None
        self._set_account_refs()
        self._trs_by_num = None

    def _set_account_refs(self):
        for ac in self.accounts.values():
            self._handle_account(ac)
        if self.root is None:
            raise ValueError("book %s has no root account." % self)
        for tr in self.transactions.values():
            self._handle_transaction(tr)

    def _handle_account(self, ac):
        if ac.parent_id is None:
            self._handle_root_ac(ac)
            return
        ac.parent = self.accounts[ac.parent_id]
        if ac.name in ac.parent.children:
            raise ValueError(("%s has two children"
                              " named %s") % (ac.parent,
                                              ac.name))
        ac.parent.children[ac.name] = ac
        if not ac.commodity:
            raise ValueError("%s's commodity is not set, "
                             "but it is not the root account" % ac)

    def _handle_transaction(self, tr):
        for sp in tr.splits.values():
            self._handle_split(sp, tr)

    def _handle_split(self, sp, tr):
        sp._account = self.accounts[sp.account_id]
        sp._transaction = tr
        sp.account.mutations.append(sp)

    def _handle_root_ac(self, ac):
        if ac.type != 'ROOT':
            print(ac.fields)
            raise ValueError("%s has no parent, but is not "
                             "of type ROOT" % ac)
        if self._root is not None:
            raise ValueError("Two root-accounts found: "
                             " %s and %s" % (self._root, ac))
        self._root = ac

    @property
    def root(self):
        return self._root

    @property
    def accounts(self):
        return self.fields['accounts']

    @property
    def transactions(self):
        return self.fields['transactions']

    @property
    def commodities(self):
        return self.fields['commodities']

    @property
    def trs_by_num(self):
        if self._trs_by_num is None:
            self._set_trs_by_num()
        return self._trs_by_num

    def _set_trs_by_num(self):
        res = {}
        for tr in self.transactions.values():
            num = tr.num
            if num not in res:
                res[num] = ()
            res[num] += (tr,)
        self._trs_by_num = res

    def tr_by_num(self, num):
        trs = self.trs_by_num[num]
        if len(trs) != 1:
            raise ValueError("there are multiple transactions, "
                             "%s, with the same number %s" %
                             (trs, num))
        return trs[0]

    def ac_by_path(self, path):
        bits = path.split(":")
        ac = self.root
        for bit in bits:
            if not bit:
                continue
            try:
                ac = ac.children[bit]
            except KeyError:
                raise KeyError("%s has no child named %s" % (
                    ac, bit))
        return ac

@six.python_2_unicode_compatible
class Account(GcObj):

    def __init__(self, fields):
        GcObj.__init__(self, fields)
        self._path = None
        self._shortpath = None
        self._shortname = None
        # the following are set by the Book
        self._parent = None
        self._children = {}
        self._mutations = []

    def __str__(self):
        return "<ac%s>" % self.nice_id

    @property
    def parent_id(self):
        return self.fields['parent']

    def get_parent(self):
        return self._parent

    def set_parent(self, value):
        self._parent = value
        self.fields['parent'] = value.id
    parent = property(get_parent, set_parent)

    @property
    def path(self):
        if self._path is None:
            self._path = self._create_path()
        return self._path

    def _create_path(self):
        if self.parent is None:
            return ""
        return ":".join((self.parent.path, self.name))

    @property
    def shortpath(self):
        if self._shortpath is None:
            self._shortpath = self._create_shortpath()
        return self._shortpath

    def _create_shortpath(self):
        if self.parent is None:
            return ""
        return ":".join((self.parent.shortpath, self.shortname))

    @property
    def name(self):
        return self.fields['name']

    @property
    def shortname(self):
        if self._shortname is None:
            if self.parent is None:
                self._shortname = ""
            self.parent._create_childrens_shortnames()
        return self._shortname

    def _create_childrens_shortnames(self):
        todo = {"": list(self.children.values())}
        while len(todo) > 0:
            shortname, acs = six.next(six.iteritems(todo))
            del todo[shortname]
            if len(acs) == 1:
                acs[0]._shortname = shortname
                continue
            for ac in acs:
                acsn = shortname + ac.name[len(shortname)]
                if acsn not in todo:
                    todo[acsn] = []
                todo[acsn].append(ac)

    @property
    def type(self):
        return self.fields['type']

    @property
    def description(self):
        return self.fields['description']

    @property
    def code(self):
        return self.fields['code']

    @property
    def commodity(self):
        return self.fields['commodity']

    @property
    def commodity_scu(self):
        return self.fields['commodity-scu']

    @property
    def children(self):
        return self._children

    @property
    def mutations(self):
        return self._mutations

    def get_descendants(self):
        todo = [self]
        while len(todo) > 0:
            desc = todo.pop()
            todo.extend(iter(desc.children.values()))
            yield desc

    def get_deep_mutations(self):
        for desc in self.get_descendants():
            for mut in desc.mutations:
                yield mut

    def get_deep_trs(self):
        trs = set()
        for mut in self.get_deep_mutations():
            trs.add(mut.transaction)
        return trs

    @property
    def nice_id(self):
        return self.path


@six.python_2_unicode_compatible
class Transaction(GcObj):

    def __init__(self, fields):
        GcObj.__init__(self, fields)

    def __str__(self):
        if self.num:
            return "tr" + self.num
        else:
            return "<tr %s %s>" % (self.date_posted, self.description)

    @property
    def splits(self):
        return self.fields['splits']

    @property
    def description(self):
        return self.fields['description']

    @property
    def num(self):
        return self.fields['num']

    @property
    def date_posted(self):
        return self.fields['date-posted']

    @property
    def date_entered(self):
        return self.fields['date-entered']

    @property
    def currency(self):
        return self.fields['currency']


@six.python_2_unicode_compatible
class Split(GcObj):

    def __init__(self, fields):
        GcObj.__init__(self, fields)
        # set by Book
        self._account = None
        self._transaction = None

    def __str__(self):
        return u"<sp %s %s by tr%s>" % (self.value,
                                        self.account.nice_id,
                                        self.transaction.num)

    @property
    def account_id(self):
        return self.fields['account']

    def get_account(self):
        return self._account

    def set_account(self, value):
        self._account = value
        self.fields['account'] = value.id
    account = property(get_account, set_account)

    @property
    def transaction(self):
        return self._transaction

    @property
    def memo(self):
        return self.fields['memo']

    @property
    def reconciled_state(self):
        return self.fields['reconciled-state']

    @property
    def quantity(self):
        return self.fields['quantity']

    @property
    def value(self):
        return self.fields['value']


class Commodity(GcStruct):

    def __init__(self, fields):
        GcStruct.__init__(self, fields)

    @property
    def id(self):
        return self.fields['id']


@six.python_2_unicode_compatible
class TimeStamp(GcStruct):

    def __init__(self, fields):
        GcStruct.__init__(self, fields)

    def __str__(self):
        return datetime.fromtimestamp(self.date).strftime("%Y-%m-%d")

    @property
    def date(self):
        return self.fields['date']

    @property
    def ns(self):
        return self.fields['ns']
