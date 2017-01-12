
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
        accounts["creditor"]=creditors_account
        for mut in dac.mutations:
            muts.append(mut_data(mut,-1))
            value -= mut.value
    except KeyError:
        pass

    try:
        cac = book.ac_by_path(creditors_account)
        accounts["debitor"]=debitors_account
        for mut in cac.mutations:
            muts.append(mut_data(mut,1))
            value += mut.value
    except KeyError:
        pass

    muts.sort(key=lambda a: a['date']['timestamp'])

    return {
            "total": value,
            "mutations": muts,
            "accounts": accounts
    }
    

def mut_data(mut, sign):
    tr = mut.transaction
    return {
            "tr": tr.num,
            "tr-description": tr.description,
            "date": {
                'text': repr(tr.date_posted),
                'timestamp': tr.date_posted.date
            },
            "description": mut.memo,
            "value": sign*mut.value
            }
