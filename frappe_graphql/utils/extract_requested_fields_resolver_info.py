from graphql import GraphQLResolveInfo

from mergedeep import merge, Strategy

from frappe_graphql.utils.depth_limit_validator import is_introspection_key
from frappe_graphql.utils.get_path import path_key
from frappe_graphql.utils.permissions import get_allowed_fieldnames_for_doctype


def collect_fields(node: dict, fragments: dict):
    """
    Inspired from https://gist.github.com/mixxorz/dc36e180d1888629cf33
    Notes:
        => Please make sure your node and fragments passed have been converted to dicts
        => Best used in conjunction with `get_allowed_fieldnames_for_doctype()`
    """

    field = {}

    if node.get('selection_set'):
        for leaf in node['selection_set']['selections']:
            if leaf['kind'] == 'field':
                field[leaf['name']['value']] = collect_fields(leaf, fragments)
            elif leaf['kind'] == 'fragment_spread':
                field.update(collect_fields(fragments[leaf['name']['value']],
                                            fragments))
    return field


def get_fields(info: GraphQLResolveInfo):
    fragments = {name: value.to_dict() for name, value in info.fragments.items()}
    fields = {}
    for field_node in info.field_nodes:
        merge(fields, collect_fields(field_node.to_dict(), fragments), strategy=Strategy.ADDITIVE)
    return fields


def get_doctype_requested_fields(
    doctype: str,
    info: GraphQLResolveInfo,
    mandatory_fields: set = None,
    parent_doctype: str = None
):
    p_key = path_key(info)
    requested_fields = info.context.get(p_key)

    if requested_fields is not None:
        return requested_fields

    selected_fields = {
        key.replace('__name', '')
        for key in get_fields(info).keys()
        if not is_introspection_key(key)
    }

    fieldnames = set(get_allowed_fieldnames_for_doctype(
        doctype=doctype,
        parent_doctype=parent_doctype
    ))

    requested_fields = selected_fields.intersection(fieldnames)
    if mandatory_fields:
        requested_fields.update(mandatory_fields)

    # send name always..
    requested_fields.add("name")

    # cache it in context..
    info.context[p_key] = requested_fields

    return list(requested_fields)
