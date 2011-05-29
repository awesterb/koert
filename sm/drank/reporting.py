import itertools

class EventReport:
	def __init__(self, event, boozedir):
		self.event = event
		self.boozedir = boozedir
	
	def generate(self):
		return itertools.chain(self._generate_shifts(),
				self._generate_beertankcount())

	def _generate_beertankcount(self):
		e = self.event
		if e.bt_deliv==None and e.btc==None:
			return
		if e.bt_deliv==None:
			yield "a beertank count (thus borrel)" \
				", but no delivery"
			return
		if e.btc==None:
			yield "a delivery, but no beertank count"
			return
		mls = e.bt_deliv.beertank
		if mls!=e.btc:
			yield "delivered beer and beertankcount do"\
					" not coincide: btc=%sml  "\
					"deliv=%sml" % (e.btc, mls)

	def _generate_shifts(self):
		shifts = self.event.shifts
		for shift in shifts:
			if shift==None:
				for line in self._on_None_shift():
					yield line
				continue
			if shift not in (1,2,3):
				yield "shiftnumber of barform #%s is not "  \
					"1, 2 or 3" % (bf.number,)
		i,j=0,0
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
	
				

