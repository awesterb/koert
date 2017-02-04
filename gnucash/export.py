import six

# returns the information (in a JSON-friendly manner)
# needed to present a user with
# its current balance based on the specified paths to
# said user's creditor and debitor account.


def get_user_balance(book, creditors_account, debitors_account):
    muts = []
    value = 0
    accounts = {}

    try:
        dac = book.ac_by_path(debitors_account)
        accounts["creditor"] = creditors_account
        for mut in dac.mutations:
            muts.append(mut_data(mut))
            value += mut.value
    except KeyError:
        pass

    try:
        cac = book.ac_by_path(creditors_account)
        accounts["debitor"] = debitors_account
        for mut in cac.mutations:
            muts.append(mut_data(mut))
            value += mut.value
    except KeyError:
        pass

    muts.sort(key=lambda a: a['date']['timestamp'])

    return {
        "total": six.text_type(value),
        "mutations": muts,
        "accounts": accounts
    }


def mut_data(mut):
    tr = mut.transaction
    return {
        "tr": tr.num,
        "tr-description": tr.description,
        "date": {
            'text': six.text_type(tr.date_posted),
            'timestamp': tr.date_posted.date
        },
        "description": mut.memo,
        "value": six.text_type(tr(mut.value))
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
