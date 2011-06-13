import itertools

class EventReport:
	def __init__(self, event, boozedir):
		self.event = event
		self.boozedir = boozedir
	
	def generate(self):
		return itertools.chain(self._check_shifts(),
				self._compare_deliv_with_btcs(),
				self._compare_bt_used_with_turfed(),
				self._check_shifts_bal())

	def _compare_deliv_with_btcs(self):
		e = self.event
		if e.bt_deliv==None and e.btc==None:
			return
		if e.bt_deliv==None:
			yield "no delivery"
			return
		if e.btc==None:
			yield "no beertank count"
			return
		mls = e.bt_deliv.beertank
		if mls!=e.btc:
			yield "delivered beer and beertankcount do"\
					" not coincide: btc=%sml  "\
					"deliv=%sml" % (e.btc, mls)
	
	def _compare_bt_used_with_turfed(self):
		u = self.event.beertank_used
		if u==None:
			return
		c = self.event.beertank_turfed
		if c==0:
			yield "no beertank use turfed"
			return
		if u!=c:
			yield "the beertank count and turfed use do" \
					" not coincide: " \
					" used=%s, turfed=%s" % (u,c)

	def _check_shifts(self):
		shifts = self.event.shifts
		for shift in shifts:
			if shift==None:
				for line in self._on_None_shift():
					yield line
				continue
			if shift not in (1,2,3):
				yield "shiftnumber of barform #%s is not "  \
					"1, 2 or 3" % (shift,)
		i=0
		j= (min([s for s in self.event.shifts if s!=None]) \
				if len(self.event.shifts)>0 else 0) -1
		while i<len(self.event.shifts) - (
				1 if None in self.event.shifts else 0):
			j += 1
			if j in self.event.barforms:
				i += 1
				continue
			yield "missing barform for shift #%s" % j
			
	def _on_None_shift(self):
		bf = self.event.barforms[None]
		yield "barform #%s of %s signed by %s has no shift number" % (
				bf.number, bf.date, bf.counter)
	
	def _check_shifts_bal(self):
		event = self.event
		shifts = event.shifts
		barforms = event.barforms
		for i in shifts:
			if i+1 not in shifts:
				continue
			eb = barforms[i].endbal
			sb = barforms[i+1].startbal
			if eb!=sb:
				yield "ending balance of shift #%s differs"\
						" from starting balance of the"\
						" following shift: %s and %s"\
						% (i, eb, sb)
