
# We often ignore the following errors
class MildErr(Exception):
	pass

class ManyMildErrs(MildErr):
	pass

# raised when, e.g., product does not appear in productdir.
class ObjDirErr(MildErr):
	def __str__(self):
		return "Unknown %s: %s" % self.args
