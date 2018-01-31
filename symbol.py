class S(str):
    # Symbol class: the only important difference between S and str is that S has a __substitute__ method
    # Note that S('a') == 'a' is True. This lets us use strings as shorthand in certain places.
    def __str__(self):
        return "S('" + super().__str__() + "')"

    def __repr__(self):
        return "S(" + super().__repr__() + ")"

    def __substitute__(self, values):
        return values[self]


def identity(x):
    return x


class TransSymbol:
    # A Symbol or SymbolicAddress with a transformation applied
    # TODO: reverse transformation currently not applied during match. Use it.
    def __init__(self, symbol, forward=identity, reverse=identity, multi=False):
        # Can either pass a single dict, or a pair of functions
        self._symbol = symbol
        self._multi = multi

        if type(forward) == dict:
            reverse = {v:k for k,v in forward.items()}
            # TODO: add option to fail on map miss
            self._forward = lambda k: forward.get(k, None)
            self._reverse = lambda k: reverse.get(k, None)
            self._map = forward
        else:
            self._forward = forward
            self._reverse = reverse
            self._map = None

    def __substitute__(self, values):
        inner = self._symbol.__substitute__(values)
        try:
            return self._forward(inner)
        except TypeError:
            # Hit if either forward function is None, or forward function receives None but doesn't handle it. Both ok.
            # TODO: figure out what I actually want the default behavior to be
            pass
        return inner

    def __eq__(self, other):
        if type(other) == TransSymbol:
            return self._symbol == other._symbol
        # TODO: probably want to match some other symbol types too.
        return False

    def __str__(self):
        return 'Trans(' + str(self._symbol) + ')'

    def __repr__(self):
        if self._map:
            return 'Trans(' + self._symbol.__repr__() + ', ' + self._map.__repr__() + ')'
        return 'Trans(' + self._symbol.__repr__() + ')'


class Nullable:
    # A simple wrapper class to mark part of a template as optional, i.e. match is allowed to fail.
    def __init__(self, contents):
        self.contents = contents
