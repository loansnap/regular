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
    def __init__(self, symbol, forward=identity, reverse=identity):
        # Can either pass a single dict, or a pair of functions
        self._symbol = symbol

        self._map = None
        if type(forward) == dict:
            reverse = {v:k for k,v in forward.items()}
            # TODO: add option to fail on map miss
            self._forward_func = lambda k: forward.get(k, None)
            self._reverse = lambda k: reverse.get(k, None)
            self._map = forward
        else:
            self._forward_func = forward
            self._reverse = reverse

    # Note that there is no corresponding wrapper for _reverse. This is a minor hack, and I haven't decided what behavior
    # I actually want here.
    def _forward(self, inner):
        try:
            return self._forward_func(inner)
        except TypeError:
            # Hit if either forward function is None, or forward function receives None but doesn't handle it. Both ok.
            # TODO: figure out what I actually want the default behavior to be
            return inner
        except AttributeError:
            # Same story
            return inner

    def __eq__(self, other):
        if type(other) == TransSymbol:
            return self._symbol == other._symbol
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
