from __future__ import print_function
from __future__ import absolute_import
from builtins import map
from builtins import str
from builtins import object
from .core import GcStruct

# Some general code concerning "difference functions".
# A *difference function*  diff  assigns to each pair A B of objects
# an object diff(A,B) with the following properties:
#   differ      A boolean which denotes whether A and B differ.
#   difference  The data of the difference.
#
# The EqDiff difference function checks whether A and B are equal.
# The Indiff difference function (which stands for indiscrete
# function and not indifferent, of course) always returns False.
#
# Let  diff  be a difference function.  This yields an obvious
# pointwise difference function on dictionaries called  DictDiff(diff).
#
# We can go deeper:
# A dictionary forms a node of a labeled tree, whose labels are the
# keys, whose leaves are the non-dictionary values and the remaining
# values (being dictionaries) are the child-nodes.
#   Recursive application of DictDiff yields a difference function
# of these trees called  DeepDictDiff(diff).


class EqDiff(object):

    def __init__(self, a, b):
        self.difference = (a, b)

    @property
    def differ(self):
        return self.difference[0] != self.difference[1]

    def __repr__(self):
        if not self.differ:
            return "(equal)"
        return "(inequal: %s vs %s)" % tuple(map(repr, self.difference))


class InDiff(object):

    def __init__(self, a, b):
        self.difference = ()
        self.differ = False


def _dictDiffit(A, B, diff):
    for k in A.keys():
        a = A[k]
        if k in B:
            b = B[k]
            d = diff(a, b)
            if diff(a, b).differ:
                yield (k, a, b, d)
        else:
            yield (k, a, None, None)
    for k in B.keys():
        b = B[k]
        if k in A:
            # we've  already met A[k] before
            continue
        else:
            yield (k, None, b, None)


def dictDiffit(diff):
    return lambda A, B: _dictDiffit(A, B, diff)


class DiffitObj(object):

    def __init__(self, A, B, diffit):
        self.diffit = diffit
        self.difference = tuple(diffit(A, B))

    def repr_diff(self, t):
        k, l, r, d = t
        if l is None:
            return "+%s (%s)" % (str(k), r)
        if r is None:
            return "-%s (%s)" % (str(k), l)
        return "~%s %s" % (k, repr(d).replace("\n", "\n  "))

    @property
    def differ(self):
        return len(self.difference) != 0

    def __repr__(self):
        if not self.differ:
            return "(no difference)"
        return "(\n%s)" % "\n".join(map(self.repr_diff,
                                        self.difference))


def Diff(diffit):
    return lambda A, B: DiffitObj(A, B, diffit)


def DictDiff(diff):
    return Diff(dictDiffit(diff))


def _DeepDiff(FP, succDiff, zeroDiff, isSucc, a, b):
    if isSucc(a, b):
        return succDiff(FP)(a, b)
    return zeroDiff(a, b)


class _DeepDiffCtx(object):

    def __init__(self, succDiff, zeroDiff, isSucc):
        self.succDiff = succDiff
        self.zeroDiff = zeroDiff
        self._succDiff_diff = succDiff(self.diff)
        self.isSucc = isSucc

    def diff(self, a, b):
        return self._succDiff_diff(a, b) if self.isSucc(a, b) \
            else self.zeroDiff(a, b)


def DeepDiff(succDiff, zeroDiff, isSucc):
    ctx = _DeepDiffCtx(succDiff, zeroDiff, isSucc)
    return ctx.diff


def DeepDictDiff(diff):
    return DeepDiff(DictDiff, diff,
                    lambda a, b: isinstance(a, dict) and isinstance(b, dict))


class _LutedDiffCtx(object):

    def __init__(self, origDiff):
        self.origDiff = origDiff
        self.lut = dict()

    def diff(self, a, b):
        d = None
        if (a, b) not in self.lut:
            d = self.origDiff(a, b)
            self.lut[(a, b)] = d
        else:
            d = self.lut[(a, b)]
        return d


def LutedDiff(diff):
    return _LutedDiffCtx(diff).diff

###############################################################################


def ShallowGcStructDiff(diff):
    return LutedDiff(lambda a, b: DeepDictDiff(diff)(a.fields, b.fields))


GcStructDiff = DeepDiff(
    ShallowGcStructDiff,
    EqDiff,
    lambda a,
    b: isinstance(
        a,
        GcStruct) and isinstance(
            b,
        GcStruct))

if __name__ == "__main__":
    print(" *** Testing koert.gnucash.diff ***")
    print("")
    dl1 = {"a": {1: "same", 2: "something", 3: "new"}, "b": 2, "q": 13}
    dl2 = {"a": {1: "same", 2: "other", 4: "new2"}, "b": 3, "c": 2}
    print("A: %s" % (dl1,))
    print("B: %s" % (dl2,))
    print("  difference:  %s" % (DeepDictDiff(EqDiff)(dl1, dl2),))
