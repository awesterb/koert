from koert.verification.core import Verifier, TrsHaveNum, TrNumsAreRemco, \
		TrNumsAreRemcoContinuous, AcMutThenNoSplit, TrMutAc, \
		SpNonZero, TrHaveFin7Softref
from koert.gnucash.tools import open_gcf
from koert.verification.fin7scheme import scheme
import sys

def main(argv):
	path = " ".join(argv[1:]).strip()
	if not path:
		print "please provide a path to a gnucash file as argument."
		return
	gcf = open_gcf(path, scheme)
	book = gcf.fields['books'].values()[0]
	v = Verifier(gcf)
	res = v.verify(TrsHaveNum, TrNumsAreRemco, TrNumsAreRemcoContinuous,
			AcMutThenNoSplit, TrMutAc, SpNonZero, 
			TrHaveFin7Softref)
	for fact in res:
		print fact
		print res[fact]
		print ""

if __name__=="__main__":
	main(sys.argv)

