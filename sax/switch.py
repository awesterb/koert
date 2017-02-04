from .core import SH


class BaseCase(object):

    def __init__(self, name, handler):
        self.name = name
        self.handler = handler


class ListCase(BaseCase):

    def __init__(self, name, handler):
        BaseCase.__init__(self, name, handler)

    def apply_result(self, result, cr):
        cr[self.name].append(result)

    def init(self, cr):
        cr[self.name] = []

    def final(self, cr):
        pass


class SingleCase(BaseCase):

    def __init__(self, name, handler, mandatory=False):
        BaseCase.__init__(self, name, handler)
        self.mandatory = mandatory

    def apply_result(self, result, cr):
        if self.name in cr:
            raise ValueError("%s has double values; " +
                             "they are %s and %s" % (self.name,
                                                     result, cr[self.name]))
        cr[self.name] = result

    def init(self, cr):
        pass

    def final(self, cr):
        if self.name not in cr:
            if self.mandatory:
                raise ValueError("The field %s is manditory, "
                                 "but hasn't been set"
                                 % self.name)
                assert(self.name in cr)
            else:
                cr[self.name] = None


class DictCase(BaseCase):

    def __init__(self, name, handler, key):
        BaseCase.__init__(self, name, handler)
        self.key = key

    def apply_result(self, result, cr):
        k = self.key(result)
        assert(k not in cr[self.name])
        cr[self.name][k] = result

    def init(self, cr):
        cr[self.name] = dict()

    def final(self, cr):
        pass


class NoCase(BaseCase):

    def __init__(self):
        BaseCase.__init__(self, "n/a", SH)

    def apply_result(self, result, cr):
        pass

    def init(self, cr):
        pass

    def final(self, cr):
        pass


NoCase = NoCase()


class SwitchSH(SH):

    def __init__(self, ot, cases, default=NoCase):
        SH.__init__(self, ot)
        self.cases = cases
        self.default = default
        self.child_results = dict()
        self.init_child_results()

    def init_child_results(self):
        for case in self.cases.values():
            case.init(self.child_results)

    def get_case(self, name):
        if name in self.cases:
            return self.cases[name]
        print("warning:  unexpected node-name %s" % name)
        return self.default

    def startElement(self, sh, name, attrs):
        return self.get_case(name).handler

    def endElement(self, sh, name, spawned_handler):
        if spawned_handler.result is None:
            return
        case = self.get_case(name)
        case.apply_result(spawned_handler.result, self.child_results)

    def goodbye(self, sh):
        for case in self.cases.values():
            case.final(self.child_results)
        self.post_result(sh, self.child_results)

    def reclaim(self):
        self.result = None
        self.child_results = dict()
        self.init_child_results()
        return True
