from graphql import GraphQLResolveInfo, is_object_type, GraphQLObjectType, is_non_null_type, \
    GraphQLNonNull, is_list_type, GraphQLList
from graphql.execution.collect_fields import collect_sub_fields
from typing import cast

from mergedeep import merge, Strategy


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
