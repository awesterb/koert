import itertools

from pricelist import PriceListErr

class EventReport:
	def __init__(self, event, boozedir):
		self.event = event
		self.boozedir = boozedir
	
	def generate(self):
		return itertools.chain(
				self._check_shifts(),
				self._compare_deliv_with_btcs(),
				self._compare_bt_used_with_turfed(),
				#self._check_shifts_bal(),
				self._compare_turfed_with_cashed()
				)

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
		for l in self.event.barforms.iterkeys():
			shifts = self.event.barforms[l].keys()
			barforms = self.event.barforms[l]
			for r in self._check_shifts_with_label(\
					l, shifts, barforms):
				yield r

	def _check_shifts_with_label(self, l, shifts, barforms):
		# Check the number of the shift.
		for shift in shifts:
			if shift==None:
				for line in self._on_None_shift(barforms):
					yield line
				continue
			if shift not in (0,1,2,3):
				yield "shiftnumber of barform #%s is not "  \
					"0, 1, 2 or 3" % (shift,)
		nice_shifts = [s for s in shifts if s!=None]
		if not nice_shifts:
			return
		m = min(nice_shifts)
		M = max(nice_shifts)
		if m > 1:
			yield "first shift with label %s has number %s (%s)" \
					% (l,m,barforms[m])
		for i in xrange(m,M+1):
			if i in barforms:
				continue
			yield "missing barform for shift %s/%s" % (l,i)
			
	def _on_None_shift(self, barforms):
		bf = barforms[None]
		yield "barform #%s of %s signed by %s has no shift number" % (
				bf.number, bf.date, bf.counter)
	
	def _check_shifts_bal(self):
		raise NotImplementedError()
		# TODO: This code still assumes Barform.shift is an int
		# instead of a Shift-instance
		event = self.event
		shifts = event.shifts
		barforms = event.barforms
		for i in shifts:
			if i==None:
				continue
			if i+1 not in shifts:
				continue
			eb = barforms[i].endbal
			sb = barforms[i+1].startbal
			if eb!=sb:
				yield "ending balance of shift #%s differs"\
						" from starting balance of the"\
						" following shift: %s and %s"\
						% (i, eb, sb)
	
	def _compare_turfed_with_cashed(self):
		event = self.event
		barforms = event.all_barforms
		for bf in barforms:
			try:
				at = bf.amount_turfed
				ac = bf.amount_cashed
			except PriceListErr as e:
				yield "could not determine the amount turfed"\
						" of barform %s (shift %s)"\
						" due to a missing price: "\
						" %s"\
						% (bf,bf.shift, e)
				continue

			extra = ""
			if at:  # is not zero
				dq = (ac-at) / at
				if abs(dq)*100<15:
					continue
				extra = ", which is %.0f%% more" % (dq*100,)
			yield "%s (shift %s)"\
					" turfed %s, but cached %s%s"\
						% (bf, bf.shift, at, ac, extra)
