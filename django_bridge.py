from django.forms.models import model_to_dict
from django.db import models

def model_to_dict_recursive(obj, filter_none=True, id_set=None):
    # TODO: this does not currently handle *-to-many relations
    if not issubclass(type(obj), models.Model):
        return obj

    # Handle loops
    if not id_set:
        id_set = {}
    id_set = set(id_set)  # Copy, so we only prevent duplicates along one path down the tree
    if obj.id in id_set:
        return obj.id
    id_set.add(obj.id)

    keys = model_to_dict(obj)
    keys['id'] = obj.id  # Omitted by model_to_dict
    if not filter_none:
        return {k:model_to_dict_recursive(obj.__getattribute__(k), filter_none, id_set) for k in keys}
    return {k:model_to_dict_recursive(obj.__getattribute__(k), filter_none, id_set) for k in keys if obj.__getattribute__(k) is not None}

# TODO: bridge back the other way
