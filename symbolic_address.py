from .format import format
from .match import match
from .merge import merge
from .simple import get_symbols
from .symbol import S, TransSymbol, Nullable

from copy import deepcopy

# See README for usage info


# Symbolic Address allows us to write things like application.borrower_profile.name, and translate it to the template
# {borrower_profile: {name: S('application.borrower_profile.name')}}
# without having to write it out.
class SymbolicAddress(object):
    def __init__(self, base_name, name=None, path=None):
        self._base_name = base_name

        # _name contains the target symbol which this address' template parses
        if name is None:
            name = base_name
        self._name = name

        # contains the template itself
        if path is None:
            path = S(self._name)
        self._path = path

    def __getattr__(self, item):
        name = self._name + '.' + item
        path = format(self._path, {S(self._name): {item: S(name)}})

        return SymbolicAddress(self._base_name, name, path)

    def __getitem__(self, item):
        if type(item) not in set([dict, list]):
            return self.__getattr__(item)

        name = self._name + '[' + str(item) + ']'
        path = format(self._path, {S(self._name): S(name)})
        return SymbolicListAddress(self._base_name, name, path, filter=item)

    def __eq__(self, other):
        if hasattr(other, '_name'):
            return self._name == other._name
        return self._name == other

    def __hash__(self):
        return self._name.__hash__()

    def __repr__(self):
        return self._name

    def __str__(self):
        return self._name

    def __substitute__(self, values):
        # First, check explicit appearance in values
        if self in values:
            return values[self]
        # Second, actually follow address
        return match(self._path, values[self._base_name]).get_single()[self._name]

    @staticmethod
    def get_expansion(mapping):
        # Take a mapping which contains symbolic addresses, and construct an explicit map for parsing the symbolic addresses
        symbols = get_symbols(mapping)

        paths = []
        for symbol in symbols:
            if type(symbol) == SymbolicAddress:
                paths.append({symbol._base_name: symbol._path})

        expansion_reverse = {}
        for path in paths:
            merge(path, expansion_reverse)
        return expansion_reverse

    @staticmethod
    def reverse_format(mapping, match_obj):
        # This method might be better called "parse"
        # NOTE: this method will NOT work with multi-field transforms.
        # That functionality requires a total overhaul of Regular, to address objects rather than just symbols.
        # A future rewrite may focus on match/replace rather than match/format, which could make this tractable.
        expansion = SymbolicAddress.get_expansion(mapping)
        return format(expansion, match_obj)


class SymbolicListAddress(SymbolicAddress):
    def __init__(self, *args, **kwargs):
        self._filter = kwargs.pop('filter', None)
        super().__init__(*args, **kwargs)

    def __getattr__(self, item):
        name = self._name + '.' + item
        filter = deepcopy(self._filter)
        filter[item] = S(name)
        path = format(self._path, {S(self._name): [filter]})

        return SymbolicAddress(self._base_name, name, path)

    # TODO: Handle repeat list indexes (i.e. indexing lists of lists). Using SymbolicAddress for this would be so awkward that I doubt anyone will do it for a while.
    def __getitem__(self, item):
        if type(item) not in set([dict, list]):
            return self.__getattr__(item)

        raise NotImplementedError

    # TODO: This could definitely be implemented in theory and could be useful, but it's tricky with the current format() implementation
    # Could be simplified by refactoring format() to replace all lists with symbols, and resolve them separately. The same helper used for that could then be used here.
    def __substitute__(self, values):
        raise NotImplementedError
