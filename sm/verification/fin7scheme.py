class scheme(object):
	avl = ":Activa:Vlottend:Liquide middelen:"
	softref_kinds_by_account_path = {
		avl+"Betaalrekening" : ["rvp"],
		avl+"Spaarrekening": ["btr"],
		avl+"Kas:Borrelkas 1": ["bk1","bk1-"],
		avl+"Borrelkas 2": ["bk2","bk2-"],
		avl+"Grote Kas": ["gk", "gk-"],
		avl+"Kleine zwarte kas":["kz","kz-"],
		avl+"Kleine rode kas" : ["kr","kr-"],
		avl+"Lolliepot" : ["lp","lp-"]
	}
