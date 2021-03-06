from .match import match, Match
from .simple import match_simple, format_simple_single, format_simple, get_symbols, NoMatchException
from .symbol import Nullable, TransSymbol

# See README for usage info


def get_singles(template):
    if type(template) == TransSymbol:
        return get_singles(template._symbol)
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
    singles = get_singles(template)  # Get symbols in the template which are NOT inside any list
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
            try:
                result += format_multi(subtemplate, match_obj)
            except NoMatchException:
                # Just don't add anything to the result list
                pass
        return result
    elif type(template) == Nullable:
        result = format_lists(template.contents, match_obj)
        if get_symbols(result):
            return Nullable(result)
        return result
    elif type(template) == TransSymbol:
        result = format_lists(template._symbol, match_obj)
        if not get_symbols(result):
            return template._forward(result)
        return TransSymbol(result, template._forward, template._reverse)
    return template


def format(template, match_obj):
    err = None
    try:
        if type(match_obj) != Match:
            # TODO: duck type for Match object
            return format_simple(template, match_obj)
        elif type(template) != list:
            return format_multi(template, match_obj)[0]

        return format_lists(template, match_obj)
    except NoMatchException as e:
        err = NoMatchException(e)
    # This *should* result in giving an error without a deep recursive stack trace into regular's internals
    raise err


def clean(template):
    if type(template) == dict:
        cleaned_template = {k: clean(v) for k,v in template.items() if not hasattr(v, '__substitute__')}
        return {k: v for k,v in cleaned_template.items() if (v is not None)}
    if type(template) == list:
        cleaned_list = [clean(e) for e in template if not hasattr(e, '__substitute__') and (e is not None)]
        cleaned_list_without_empty_dicts = [e for e in cleaned_list if (e != {})]
        return cleaned_list_without_empty_dicts
    if type(template) == Nullable:
        return clean(template.contents)
    if type(template) == TransSymbol:
        return clean(template._forward(clean(template._symbol)))
    if hasattr(template, '__substitute__'):
        return None
    return template
