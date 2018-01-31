from .symbol import Nullable, TransSymbol

class NoMatchException(Exception):
    pass

class Everything:
    def __contains__(self, item):
        return True
everything = Everything()

def get_default(obj, key):
    # Equivalent of .get(key, None) on dicts, but works on non-dicts.
    try:
        return obj[key]
    except:
        pass

    try:
        return obj.__getattribute__(key)
    except:
        return None

def unique(matches):
    # TODO: write a not-terrible unique function. Requires recursively changing dicts to something hashable.
    result = []
    for m in matches:
        if not m in result:
            result.append(m)
    return result

def cartesian(partials):
    # Each 'partial' is a list of possible value maps for some subset of the symbols
    # ex.: [[{'a':1},{'a':2}], [{'b':3},{'b':4}]] -> [{'a':1,'b':3},{'a':1,'b':4},{'a':2,'b':3},{'a':2,'b':4}]
    if len(partials) == 0:
        return []
    if len(partials) == 1 and len(partials[0]) == 0:
        # Annoying corner case, I should probably handle uniqueing earlier so it's not needed
        return [{}]
    if len(partials) == 1:
        return partials[0]
    if len(partials[0]) == 0:
        # This lets match_simple handle parts of the data which don't contain any relevant symbols.
        # TODO: refactor so it doesn't need special handling. Will probably involve uniqueing  earlier.
        return cartesian(partials[1:])

    result = []
    for remainder in cartesian(partials[1:]):
        for candidate in partials[0]:
            # If the two symbol sets have any symbols in common, then match on their values
            # TODO: make this more efficient
            common = set(remainder).intersection(candidate)
            if {k: remainder[k] for k in common} != {k: candidate[k] for k in common}:
                continue

            # The "cartesian" part
            full = {k:v for k,v in remainder.items()}
            full.update(candidate)
            result.append(full)
    return result

def match_simple(template, data, symbols=everything):
    if not symbols:
        # Corner case, never reached by recursion.
        return [{}]
    if hasattr(template, '__substitute__') and template in symbols:
        return [{template: data}]
    elif hasattr(template, '__substitute__'):
        return []
    elif type(template) == Nullable:
        try:
            return match_simple(template.contents, data, symbols)
        except:
            return []

    partials = []
    if type(template) == TransSymbol:
        partials.append(match_simple(template._symbol, template._reverse(data), symbols))
    elif type(template) == dict:
        for key in template:
            partials.append(match_simple(template.get(key, None), get_default(data, key), symbols))
    elif type(template) == list:
        for target_element in template:
            matches = []
            found_match = False
            for candidate_element in (data or []):
                try:
                    # attempt match; error means no match
                    # Note: can return something empty *without* an error; this means match is successful, there just weren't any symbols
                    matches += match_simple(target_element, candidate_element, symbols)
                    found_match = True
                except:
                    continue
            if not found_match:
                # TODO: find some library to serialize stuff into something short but useful.
                raise NoMatchException(target_element)
            partials.append(matches)
    elif template != data:
        raise NoMatchException()

    #print(partials)
    return unique(cartesian(partials))

def get_symbols(template):
    if type(template) == TransSymbol:
        return get_symbols(template._symbol)
    if hasattr(template, '__substitute__'):
        return [template]
    if type(template) == list:
        return sum([get_symbols(v) for v in template], [])
    if type(template) == dict:
        return sum([get_symbols(v) for v in template.values()], [])
    if type(template) == Nullable:
        return get_symbols(template.contents)
    return []

def format_simple_single(template, values):
    if type(template) == dict:
        return {key: format_simple_single(val, values) for key, val in template.items()}
    elif type(template) == list:
        return [format_simple_single(element, values) for element in template]
    elif type(template) == Nullable:
        result = format_simple_single(template.contents, values)
        if get_symbols(result):
            return Nullable(result)
        return result
    elif type(template) == TransSymbol:
        result = format_simple_single(template._symbol, values)
        if not get_symbols(result):
            return template._forward(result)
        return TransSymbol(result, template._forward, template._reverse)

    try:
        return template.__substitute__(values)
    except AttributeError:
        # Duck typing here, failure is normal.
        # TODO: duck type in place of dict and list checks, too
        pass
    except KeyError:
        # Hit for any symbols we're not substituting, failure normal
        pass

    return template

def format_simple(template, matches):
    if type(matches) == list:
        return [format_simple_single(template, m) for m in matches]
    return format_simple_single(template, matches)
