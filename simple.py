from .symbol import Nullable, TransSymbol

class Everything:
    def __contains__(self, item):
        return True
everything = Everything()

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
            full = {k:v for k,v in remainder.items()}
            full.update(candidate)
            result.append(full)
    return result

def match_simple(template, data, symbols=everything):
    if not symbols:
        # Corner case, never reached by recursion.
        return [{}]
    if type(template) == TransSymbol and (template in symbols or template._symbol in symbols):
        return [{template._symbol: template._reverse(data)}]
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
    if type(template) == dict:
        for key in template:
            partials.append(match_simple(template.get(key, None), data.get(key, None), symbols))
    elif type(template) == list:
        for target_element in template:
            matches = []
            found_match = False
            for candidate_element in data:
                try:
                    # attempt match; error means no match
                    # Note: can return something empty *without* an error; this means match is successful, there just weren't any symbols
                    matches += match_simple(target_element, candidate_element, symbols)
                    found_match = True
                except:
                    continue
            if not found_match:
                # TODO: find some library to serialize stuff into something short but useful.
                #raise Exception("No match: " + str(target_element) + " vs " + str(data))
                raise Exception("No match!")
            partials.append(matches)
    elif template != data:
        #raise Exception("No match: " + str(template) + " vs " + str(data))
        raise Exception("No match!")

    #print(partials)
    return unique(cartesian(partials))

def get_symbols(template):
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
