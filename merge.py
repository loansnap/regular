from .simple import get_default
from copy import deepcopy


def set_general(target, key, value):
    try:
        target[key] = value
    except:
        target.__setattr__(key, value)
    return


# TODO: next iteration of Regular should roll this capability directly into match/format
# TODO: Check that merge() correctly handles Nullable & TransformationSymbol
def merge(source, target):
    if type(source) == dict:
        for k in source:
            new_target = get_default(target, k)
            if not new_target:
                # Note: it should generally be assumed that the "source" for merge is a lists-and-dicts structure derived from a template, so deepcopy() works fine.
                set_general(target, k, deepcopy(source[k]))
            else:
                merge(source[k], new_target)
    elif type(source) == list:
        for source_item in source:
            found_match = False
            for target_item in target:
                try:
                    # attempt match; error means no match
                    merge(source_item, target_item)  # TODO: this will mess things up if it writes something and then hits a "no match"; need to check for match separately
                    found_match = True
                    break
                except:
                    continue
            if not found_match:
                raise Exception("No match: " + str(source_item) + " vs " + str(target))
        return
        pass
    elif source != target:
        raise Exception("No match!")
    return target
