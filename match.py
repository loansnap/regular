from .simple import match_simple, NoMatchException

# See README for usage info


def match(template, data):
    # For a full parse, the value of a symbol depends on the value of other symbols higher in the tree.
    # Our problem is to represent all those values and dependencies efficiently.
    # So, we do the obvious thing and just punt the whole problem.
    return Match(template, data)

def can_match(template, data):
    # WARNING: THIS METHOD WILL COMPUTE ALL POSSIBLE MATCHES
    try:
        match_simple(template, data)
    except NoMatchException:
        return False
    return True


class Match(object):
    def __init__(self, template, data):
        self.template = template
        self.data = data

    # TODO: Work out a more coherent behavior for the standard methods on Match objects
    def __iter__(self):
        return (m for m in match_simple(self.template, self.data))

    def __getitem__(self, item):
        return match_simple(self.template, self.data, symbols=[item])[0]

    def get_single(self):
        # WARNING: THIS METHOD WILL COMPUTE ALL POSSIBLE MATCHES
        # Todo: make match_simple an iterator, so methods like this one can be more efficient.
        return match_simple(self.template, self.data)[0]
