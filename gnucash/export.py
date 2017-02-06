import six

# returns the information (in a JSON-friendly manner)
# needed to present a user with
# its current balance based on the specified paths to
# said user's creditor and debitors accounts.


def get_user_balance(book, accounts):
    trs = set([])
    accounts = set(accounts)
    accounts_to_remove = set()

    for account in accounts:
        try:
            ac = book.ac_by_path(account)
        except KeyError:
            accounts_to_remove.add(account)
            continue
        for mut in ac.mutations:
            trs.add(mut.transaction)
    accounts -= accounts_to_remove

    trs = list(trs)

    trs.sort(key=lambda a: a.date_posted.date)

    sumptr = [0]
    trs = [tr_data(tr, accounts, sumptr) for tr in trs]

    # MsgPack can't serialize sets
    accounts = dict([(account, None) for account in accounts])

    return {
        "total": six.text_type(sumptr[0]),
        "trs": trs,
        "accounts": accounts
    }


def tr_data(tr, accounts, sumptr):
    before = sumptr[0]
    return {
        "num": tr.num,
        "description": tr.description,
        "date": {
            'text': six.text_type(
                tr.date_posted),
            'timestamp': tr.date_posted.date},
        "muts": [
            mut_data(
                mut,
                accounts,
                sumptr) for mut in six.itervalues(
                tr.splits)],
        "value": six.text_type(sumptr[0] - before),
        "sum": six.text_type(sumptr[0])}


def mut_data(mut, accounts, sumptr):
    path = mut.account.path
    counts = (path in accounts)
    if counts:
        sumptr[0] += mut.value
    return {
        "memo": mut.memo,
        "value": six.text_type(mut.value),
        "account": path,
        "counts": counts,
        "sum": six.text_type(sumptr[0])
    }


def get_debitors(book, accounts):
    result = dict()

    for path in accounts:
        ac = book.ac_by_path(path)
        for name in ac.children:
            if name not in result:
                result[name] = 0
            for mut in ac.children[name].mutations:
                result[name] += mut.value

    result = [(name, result[name]) for name in result]
    result.sort(key=lambda x: -x[1])

    result = [(name, six.text_type(val)) for (name, val) in result if val > 0]

    return result
