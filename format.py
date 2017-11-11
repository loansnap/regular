from .match import match, Match
from .simple import match_simple, format_simple_single, format_simple, get_symbols
from .symbol import Nullable

# See README for usage info


def get_singles(template):
    if hasattr(template, '__substitute__'):
        return [template]
    if type(template) == list:
        return []
    if type(template) == dict:
        return sum([get_singles(v) for v in template.values()], [])
    if type(template) == Nullable:
        return get_singles(template.contents)
    return []


def format_multi(template, match_obj):
    # Assumption: outermost level of template is NOT a list.
    singles = get_singles(template)
    matches = match_simple(match_obj.template, match_obj.data, symbols=singles)
    # print(singles, matches)

    results = []
    for matched in matches:
        new_match_template = format_simple_single(match_obj.template, matched)
        new_match_obj = match(new_match_template, match_obj.data)

        new_template = format_simple_single(template, matched)
        # print("pre-list-format result:", new_template, new_match_template)
        results.append(format_lists(new_template, new_match_obj))
    return results


def format_lists(template, match_obj):
    # Assumption: there should be no symbols outside of lists in template
    # As long as that assumption holds, it's time to call format_lists
    if type(template) == dict:
        return {k: format_lists(v, match_obj) for k, v in template.items()}
    elif type(template) == list:
        result = []
        for subtemplate in template:
            result += format_multi(subtemplate, match_obj)
        return result
    elif type(template) == Nullable:
        result = format_lists(template.contents, match_obj)
        if get_symbols(result):
            return Nullable(result)
        return Nullable(result)
    return template


def format(template, match_obj):
    if type(match_obj) != Match:
        # TODO: duck type for Match object
        return format_simple(template, match_obj)
    elif type(template) != list:
        return format_multi(template, match_obj)[0]

    return format_lists(template, match_obj)


def clean(template):
    if type(template) == dict:
        return {k: clean(v) for k,v in template.items() if not hasattr(v, '__substitute__') and (v is not None)}
    if type(template) == list:
        return [clean(e) for e in template]
    if type(template) == Nullable:
        return clean(template.contents)
    return template
