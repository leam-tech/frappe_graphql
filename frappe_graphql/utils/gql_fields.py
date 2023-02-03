import jmespath
from graphql import GraphQLResolveInfo

from mergedeep import merge, Strategy

from frappe_graphql.utils.introspection import is_introspection_key
from frappe_graphql.utils import get_info_path_key
from frappe_graphql.utils.permissions import get_allowed_fieldnames_for_doctype


def collect_fields(node: dict, fragments: dict):
    """
    Recursively collects fields from the AST
    Inspired from https://gist.github.com/mixxorz/dc36e180d1888629cf33

    Notes:
        => Please make sure your node and fragments passed have been converted to dicts
        => Best used in conjunction with `get_allowed_fieldnames_for_doctype()`

    Args:
        node (dict): A node in the AST
        fragments (dict): Fragment definitions
    Returns:
        A dict mapping each field found, along with their sub fields.
        {'name': {},
         'sentimentsPerLanguage': {'id': {},
                                   'name': {},
                                   'totalSentiments': {}},
         'slug': {}}
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


def get_field_tree_dict(info: GraphQLResolveInfo):
    """
    A hierarchical dictionary of the graphql resolver fields nodes merged and returned.
    Args:
        info (GraphQLResolveInfo): GraphqlResolver Info
    Returns:
        A dict mapping each field found, along with their sub fields.
        {'name': {},
         'sentimentsPerLanguage': {'id': {},
                                   'name': {},
                                   'totalSentiments': {}},
         'slug': {}}
    """
    fragments = {name: value.to_dict() for name, value in info.fragments.items()}
    fields = {}
    for field_node in info.field_nodes:
        merge(fields, collect_fields(field_node.to_dict(), fragments), strategy=Strategy.ADDITIVE)
    return fields


def get_doctype_requested_fields(
    doctype: str,
    info: GraphQLResolveInfo,
    mandatory_fields: set = None,
    parent_doctype: str = None,
    jmespath_str: str = None
):
    """
    Returns the list of requested fields for the given doctype from a GraphQL query.

    :param doctype: The doctype to retrieve requested fields for.
    :type doctype: str

    :param info: The GraphQLResolveInfo object representing information about a
        resolver's execution.
    :type info: GraphQLResolveInfo

    :param mandatory_fields: A set of fields that should always be included in the returned list,
        even if not requested.
    :type mandatory_fields: set

    :param parent_doctype: The doctype of the parent object, if any.
    :type parent_doctype: str

    :param jmespath_str: The jmespath string leading to the return type of the specified doctype.
    :type jmespath_str: str

    :return: The list of requested fields for the given doctype.
    :rtype: list of str
    """
    p_key = get_info_path_key(info)
    requested_fields = info.context.get(p_key)

    if requested_fields is not None:
        return requested_fields

    field_tree = get_field_tree_dict(info)
    if jmespath_str:
        expression = jmespath.compile(jmespath_str)
        field_tree = expression.search(field_tree)

    selected_fields = {
        key.replace('__name', '')
        for key in (field_tree or {}).keys()
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
