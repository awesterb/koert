import six

# returns the information (in a JSON-friendly manner)
# needed to present a user with
# its current balance based on the specified paths to
# said user's creditor and debitors accounts.


def get_user_balance(book, accounts):
    trs = set([])
    accounts = set(accounts)
    value = 0

    for account in accounts:
        try:
            ac = book.ac_by_path(account)
        except KeyError:
            accounts.delete(account)
            continue
        for mut in ac.mutations:
            trs.add(mut.transaction)
            value += mut.value

    trs = list(trs)

    trs.sort(key=lambda a: a.date_posted.date)

    trs = [tr_data(tr, accounts) for tr in trs]

    # MsgPack can't serialize sets
    accounts = dict([(account, None) for account in accounts])

    return {
        "total": six.text_type(value),
        "trs": trs,
        "accounts": accounts
    }


def tr_data(tr, accounts):
    return {
        "tr": tr.num,
        "description": tr.description,
        "date": {
            'text': six.text_type(tr.date_posted),
            'timestamp': tr.date_posted.date
        },
        "muts": [mut_data(mut, accounts) for mut in six.itervalues(tr.splits)]
    }


def mut_data(mut, accounts):
    path = mut.account.path
    return {
        "memo": mut.memo,
        "value": six.text_type(mut.value),
        "account": path,
        "counts": (path in accounts)
    }


def get_debitors(book, creditors_account, debitors_account):
    result = []
    names = set()

    cac = book.ac_by_path(creditors_account)
    names.update(iter(cac.children.keys()))

    dac = book.ac_by_path(debitors_account)
    names.update(iter(dac.children.keys()))

    for name in names:
        value = 0
        if name in cac.children:
            for mut in cac.children[name].mutations:
                value += mut.value
        if name in dac.children:
            for mut in dac.children[name].mutations:
                value += mut.value
        if value > 0:
            result.append((name, value))

    result.sort(key=lambda x: -x[1])

    result = [(name, six.text_type(val)) for (name, val) in result]

    return result
