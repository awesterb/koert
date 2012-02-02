
class Header:
	def __init__(self, name, proj):
		self.name = name
		self.proj = proj


class Table:
	def __init__(self, headers, rows):
		self.headers = headers
		self.rows = rows

	def format(self):
		# Get a matrix of strings
		rows_str = [map(lambda h: h.name, self.headers)]
		for r in self.rows:
			rows_str.append(map(lambda h: h.proj(r), self.headers))
		return StringMatrix(rows_str).format()
		

class StringMatrix:
	def __init__(self, rows):
		self.rows = rows
		self.add_padding()
	
	def add_padding(self,):
		rows = self.rows
		if not rows:
			return  # no rows,  no padding
		example = rows[0]
		# Get the maximal length of the strings per column
		maxs = map(lambda i: max([len(r[i]) for r in rows]),
				range(len(example)))
		# Add padding to make the lengths equal
		for i in xrange(len(rows)):
			row = rows[i]
			for j in xrange(len(row)):
				row[j] += (maxs[j]-len(row[j])) * " "
	
	def format(self, col_sep="  ", row_sep="\n"):
		return row_sep.join([col_sep.join(r) for r in self.rows])
	
	
		
		
