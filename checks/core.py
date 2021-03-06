import six

from datetime import date


def check_split_direction(book, split):
    return split.account.mutation_sign * split.value < 0


def check_split_account_children(book, split):
    return len(split.account.children) > 0


def check_split_value_zero(book, split):
    return split.value == 0 and not split.transaction.is_census


def check_tr_splitcount(book, tr):
    return len(list(tr.splits)) <= 1 and not tr.is_census


def check_tr_period(book, tr):
    start = book.meta['period']['from']
    end = book.meta['period']['to']
    return tr.date_posted.date < start or tr.date_posted.date > end


def check_tr_in_future(book, tr):
    return tr.date_posted.date > date.today()


def check_tr_has_number(book, tr):
    return tr.num is None


def check_tr_unique_number(book, tr):
    return len(book.trs_by_num[tr.num]) != 1

def check_tr_census(book, tr):
    if not tr.is_census or tr.census==None:
        return False
    for sp in six.itervalues(tr.splits):
        ad = sp.account.days[tr.day]
        if ad.starting_balance == tr.census or ad.ending_balance == tr.census:
            return False
        # perhaps the desired number appears in the middle of the day
        total = ad.starting_balance
        trs = list(ad.transactions)
        trs.sort(key=lambda tr: tr.num)
        for tr_ in trs:
            for sp_ in six.itervalues(tr_.splits):
                if sp_.account == sp.account:
                    total += sp_.value
                if total == tr.census:
                    return False
    return True

def check_tr_census_wellformed(book, tr):
    if not tr.is_census:
        return False
    return tr.census==None

def check_day_balance_sign(book, day):
    return day.ending_balance * day.account.balance_sign < 0


def check_all(book, names=()):
    for check in CHECKS:
        if len(names)>0 and check['name'] not in names:
            continue
        for obj in _CHECK_ALL_SWITCH[check['per']](book, check):
            yield {'object': obj, 'check': check}

def mark_all(book):
    for check in CHECKS:
        book.checks[check['name']] = { 'check': check, 'objects':[] }
    for result in check_all(book):
        result['object'].checks.append(result['check'])
        book.checks[result['check']['name']]['objects'].append(result['object'])

def check_all_splits(book, check):
    for tr in six.itervalues(book.transactions):
        for split in six.itervalues(tr.splits):
            if check['func'](book, split):
                yield split


def check_all_transactions(book, check):
    for tr in six.itervalues(book.transactions):
        if check['func'](book, tr):
            yield tr


def check_all_account_days(book, check):
    for ac in six.itervalues(book.accounts):
        for day in six.itervalues(ac.days):
            if check['func'](book, day):
                yield day


_CHECK_ALL_SWITCH = {
    'split': check_all_splits,
    'transaction': check_all_transactions,
    'account-day': check_all_account_days,
}

CHECKS = [
    {
        'name': "W01",
        'func': check_split_direction,
        'description': 'Wrong side?',
        'type': 'warning',
        'per': 'split',
    },
    {
        'name': "E01",
        "func": check_split_account_children,
        'description': "Mutates account with children!",
        'type': 'error',
        'per': 'split',
    },
    {
        'name': "W02",
        'func': check_split_value_zero,
        'description': "Shouldn't be zero?",
        'type': "warning",
        "per": "split"
    },
    {
        'name': "E02",
        'func': check_tr_splitcount,
        'description': "Missing some splits!",
        'type': "error",
        "per": "transaction"
    },
    {
        'name': "E03",
        'func': check_tr_period,
        'description': "Not in booking period!",
        'type': "error",
        "per": "transaction"
    },
    {
        'name': "W03",
        'func': check_tr_in_future,
        'description': "In the future?",
        'type': "warning",
        "per": "transaction"
    },
    {
        'name': "E03",
        'func': check_tr_has_number,
        'description': "No transaction number!",
        'type': "error",
        "per": "transaction"
    },
    {
        'name': "E04",
        'func': check_tr_unique_number,
        'description': "Another transaction has the same number!",
        'type': "error",
        "per": "transaction"
    },
    {
        'name': "W04",
        'func': check_day_balance_sign,
        'description': "Is such a balance possible?",
        'type': "warning",
        "per": "account-day"
    },
    {
        'name': "E05",
        'func': check_tr_census,
        'description': "Census does not match any balance this day!",
        'type': 'error',
        'per': 'transaction'
    },
    {
        'name': "W05",
        'func': check_tr_census_wellformed,
        'description': "Is this a census? If so, it does not make sense to me.",
        'type': 'warning',
        'per': 'transaction'
    },
]
