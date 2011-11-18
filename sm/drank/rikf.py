import csv

class yaExcelDialect(csv.Dialect):
	delimiter = ";"
	quotechar = '"'
	doublequote = True
	skipinitialspace = False
	lineterminator = "\r\n"
	quoting = csv.QUOTE_MINIMAL

def read_rikf(f):
	for line in csv.reader(comment_stripper(f), 
			dialect = yaExcelDialect):
		line = strip_line(line)
		if line==None:
			continue
		yield line

def strip_line(line):
	line = map(lambda s: s.strip(), line)
	i = len(line)
	while i>0 and line[i-1]=="":
		i -= 1
	if i==0:
		return None
	return line[:i]

class RikfErr(Exception):
	def __str__(self):
		return "while parsing '%s' at line %s: %s" % self.args

def open_rikf_ar(p):
	with open(p) as f:
		res = []
		ln = 1
		try:
			for x in read_rikf(f):
				ln += 1
				res.append(x)
		except csv.Error as e:
			raise RikfErr(p, ln+1, e)
		return res


def comment_stripper(f):
	for line in f:
		decom = line.split("#",1)[0].strip()
		if len(decom)==0:
			continue
		yield decom
		
