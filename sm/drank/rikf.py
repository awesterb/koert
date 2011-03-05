import csv

class yaExcelDialect(csv.Dialect):
	delimiter = ";"
	quotechar = '"'
	doublequote = True
	skipinitialspace = False
	lineterminator = "\r\n"
	quoting = csv.QUOTE_MINIMAL

def open_rikf(p):
	return read_rikf(open(p))

def read_rikf(f):
	return csv.reader(comment_stripper(f), dialect = yaExcelDialect)

def comment_stripper(f):
	for line in f:
		if len(line)==0:
			yield line
			continue
		if line[0]=="#":
			continue
		yield line
