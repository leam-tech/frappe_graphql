from graphql import GraphQLResolveInfo


def collect_fields(node: dict, fragments: dict):
    """
    Inspired from https://gist.github.com/mixxorz/dc36e180d1888629cf33
    Notes:
        => Please make sure your node and fragments passed have been converted to dicts
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
    node = info.field_nodes[0].to_dict()
    fragments = {name: value.to_dict() for name, value in info.fragments.items()}
    return collect_fields(node, fragments)


def get_selected_fields_for_cursor_paginator_node(info: GraphQLResolveInfo):
    """
    we know how the structure looks like based on the specs
    https://relay.dev/graphql/connections.htm

    We are only concerned with the fields we are fetching from the db
    Note:
        => We will be avoiding __schema, __type, and __typename
        => We will not be sending __name as we define these link fields
    """
    import jmespath
    black_listed_fields = ("__schema", "__type", "__typename")
    expression = jmespath.compile("edges.node.keys(@)")
    fields = get_fields(info)
    # maybe the following can be done in jmespath =)
    return [field.replace('__name', '') for field in expression.search(fields) or [] if
            field not in black_listed_fields]


def extract_field_node_from_cursor_paginator(info: GraphQLResolveInfo) -> dict:
    """
    Basically the node which the user specified what fields they need..
    """
    import jmespath
    expression = jmespath.compile(
        "selection_set.selections[?name.value == 'edges'] |[0].selection_set.selections[?name.value == 'node'] | [0]")  # noqa
    return expression.search(info.field_nodes[0].to_dict())
