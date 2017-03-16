import six
from datetime import datetime
from decimal import Decimal


class GcStruct(object):

    def __init__(self, fields):
        self.fields = fields


class GcObj(GcStruct):

    def __init__(self, fields):
        GcStruct.__init__(self, fields)
        self._checks = None

    @property
    def checks(self):
        if self._checks == None:
            self._checks = []
        return self._checks

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
        self._obj_by_id = None
        self._checks = {}

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
        if tr.id not in sp.account._transactions_ids:
            sp.account.transactions.append(tr)
            sp.account._transactions_ids.add(tr.id)

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

    @property
    def obj_by_id(self):
        if self._obj_by_id is None:
            self._set_obj_by_id()
        return self._obj_by_id

    def _set_obj_by_id(self):
        objs = {}
        for tr in self.transactions.values():
            objs[tr.id] = tr
            for sp in six.itervalues(tr.splits):
                objs[sp.id] = sp
        for ac in self.accounts.values():
            objs[ac.id] = ac
        self._obj_by_id = objs

    def tr_by_num(self, num):
        trs = self.trs_by_num[num]
        if not trs:
            raise KeyError()
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

    def apply_census_token(self, token):
        for tr in six.itervalues(self.transactions):
            if tr.description.startswith(token):
                tr.is_census = True

    def obj_by_handle(self, handle):
        if handle == "" or handle.startswith(":"):
            return (self.ac_by_path(handle),)
        if handle.startswith("tr"):
            return self.trs_by_num.get(handle[2:], ())
        if handle.startswith("id"):
            obj = self.obj_by_id.get(handle[2:])
            return (obj,) if obj is not None else ()
        if handle.startswith("day"):
            day, path = handle[3:].split(":",1)
            path = ":"+path
            return (self.ac_by_path(path).days[day],)


ACCOUNT_SIGNS = {
    'CASH': {
        'balance': 1,
        'mutation': 0,
    },
    'BANK': {
        'balance': 1,
        'mutation': 0
    },
    'EQUITY': {
        'balance': 0,
        'mutation': 0
    },
    'EXPENSE': {
        'balance': 1,
        'mutation': 1
    },
    'ASSET': {
        'balance': 1,
        'mutation': 0,
    },
    'INCOME': {
        'balance': -1,
        'mutation': -1,
    },
    'LIABILITY': {
        'balance': -1,
        'mutation': 0
    },
    'PAYABLE': {
        'balance': -1,
        'mutation': 0
    },
    'ROOT': {
        'balance': 0,
        'mutation': 0
    }
}


@six.python_2_unicode_compatible
class Account(GcObj):

    def __init__(self, fields):
        GcObj.__init__(self, fields)
        self._path = None
        self._shortpath = None
        self._shortname = None
        self._days = None
        # the following are set by the Book
        self._parent = None
        self._children = {}
        self._transactions = []
        self.is_opening_balance = False
        self._opening_balance = None
        self._balance = None
        self._transactions_ids = set()

    @property
    def handle(self):
        return self.path

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
        for tr in self._transactions:
            for split in tr.splits.values():
                if split.account == self:
                    yield split

    @property
    def transactions(self):
        return self._transactions

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

    @property
    def days(self):
        if not self._days:
            self._create_days()
        return self._days

    @property
    def opening_day(self):
        return self.days[""]

    def _create_days(self):
        days = dict()
        days[""] = AccountDay("", self)
        for tr in self.transactions:
            day = tr.day
            if day not in days:
                days[day] = AccountDay(day, self)
            days[day].transactions.append(tr)
            for split in six.itervalues(tr.splits):
                if split.account == self:
                    days[day].value += split.value

        self._days = days

        keys = sorted(six.iterkeys(days))
        previous = None
        for key in keys:
            days[key].previous_day = previous
            if previous is not None:
                previous.next_day = days[key]
                days[key].starting_balance = previous.ending_balance
            else:
                days[key].starting_balance = Decimal(0)
            previous = days[key]

    @property
    def mutation_sign(self):
        if self.type not in ACCOUNT_SIGNS:
            raise KeyError('unknown account type %r' % (self.type,))
        return ACCOUNT_SIGNS[self.type]['mutation']

    @property
    def balance_sign(self):
        if self.type not in ACCOUNT_SIGNS:
            raise KeyError('unknown account type %r' % (self.type,))
        return ACCOUNT_SIGNS[self.type]['balance']

    def get_balance_on(self, day):
        total = Decimal(0)
        for child in six.itervalues(self.children):
            total += child.get_balance_on(day)
        return total + self.get_last_acday_before(day).ending_balance

    def get_last_acday_before(self, day):
        acday = self.opening_day
        while True:
            nextad = acday.next_day
            if nextad == None or nextad.is_after(day):
                return acday
            acday = nextad

    @property
    def opening_balance(self):
        if self._opening_balance==None:
            self._opening_balance = self.get_balance_on("")
        return self._opening_balance

    @property
    def balance(self):
        if self._balance==None:
            self._balance = self.get_balance_on(None)
        return self._balance

@six.python_2_unicode_compatible
class AccountDay:

    def __init__(self, day, account):
        self.day = day
        self.account = account
        self.transactions = []
        self.value = Decimal(0)
        self.previous_day = None
        self.next_day = None
        self.starting_balance = None
        self._checks = None

    @property
    def handle(self):
        return "day%s%s" % (self.day, self.account.path)

    @property
    def checks(self):
        if self._checks == None:
            self._checks = []
        return self._checks

    @property
    def ending_balance(self):
        return self.starting_balance + self.value

    def __str__(self):
        return "<%s of %s>" % (self.day, self.account.path)

    def is_after(self, day):
        if day==None:
            return False
        if day=="":
            return self.day!=""
        return datetime.strptime(self.day, "%Y-%m-%d") < \
                datetime.strptime(day, "%Y-%m-%d")


@six.python_2_unicode_compatible
class Transaction(GcObj):

    def __init__(self, fields):
        GcObj.__init__(self, fields)
        self._day = None
        self.is_census = False

    def __str__(self):
        if self.num:
            return "tr" + self.num
        else:
            return "<tr %s %s>" % (self.date_posted, self.description)

    @property
    def handle(self):
        if self.num:
            return "tr" + self.num
        else:
            return "id" + self.id


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

    @property
    def day(self):
        if self._day is None:
            self._create_day()
        return self._day

    def _create_day(self):
        for split in six.itervalues(self.splits):
            if split.account.is_opening_balance:
                self._day = ""
                return
        self._day = six.text_type(self.date_posted)


@six.python_2_unicode_compatible
class Split(GcObj):

    def __init__(self, fields):
        GcObj.__init__(self, fields)
        # set by Book
        self._account = None
        self._transaction = None

    @property
    def handle(self):
        return "id" + self.id

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
        return self.datetime.strftime("%Y-%m-%d")

    @property
    def datetime(self):
        return datetime.fromtimestamp(self.timestamp)

    @property
    def date(self):
        return self.datetime.date()

    @property
    def timestamp(self):
        return self.fields['date']

    @property
    def ns(self):
        return self.fields['ns']
