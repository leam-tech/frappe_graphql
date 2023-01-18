from graphql import GraphQLResolveInfo


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
    node = info.field_nodes[0].to_dict()
    fragments = {name: value.to_dict() for name, value in info.fragments.items()}
    return collect_fields(node, fragments)